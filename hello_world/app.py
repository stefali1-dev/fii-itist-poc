import json
import os
import boto3
import uuid
from datetime import datetime
import base64
import re
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')


def _html_form_page() -> str:
    return """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\"> 
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\"> 
    <title>Welcome</title>
    <style>
      :root { --bg:#0b132b; --card:#1c2541; --accent:#5bc0be; --text:#eaeaea; }
      * { box-sizing: border-box; }
      body { margin:0; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,'Helvetica Neue',Arial,'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol'; background: var(--bg); color: var(--text); }
      .wrap { min-height: 100dvh; display: grid; place-items: center; padding: 24px; }
      .card { width: 100%; max-width: 560px; background: var(--card); border-radius: 16px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,.3); }
      h1 { margin: 0 0 8px; font-size: clamp(24px, 6vw, 36px); }
      p { margin: 0 0 20px; opacity: .85; }
      label { display:block; font-weight: 600; margin-bottom: 8px; font-size: clamp(16px, 4vw, 18px); }
      input[type=text] { width: 100%; font-size: clamp(18px, 5vw, 22px); padding: 16px 18px; border-radius: 12px; border: 2px solid transparent; outline: none; background: #111827; color: var(--text); transition: border-color .2s, box-shadow .2s; }
      input[type=text]:focus { border-color: var(--accent); box-shadow: 0 0 0 4px rgba(91,192,190,.2); }
      button { margin-top: 18px; width: 100%; font-size: clamp(18px, 5vw, 22px); padding: 16px 18px; border-radius: 12px; border: none; background: var(--accent); color: #0b132b; font-weight: 700; cursor: pointer; box-shadow: 0 6px 14px rgba(91,192,190,.25); }
      button:active { transform: translateY(1px); }
      .msg { margin-top: 12px; font-size: 16px; min-height: 24px; }
    </style>
  </head>
  <body>
    <div class=\"wrap\">
      <div class=\"card\">
        <h1>Hello</h1>
        <p>Enter your name and submit.</p>
        <form id=\"form\" novalidate>
          <label for=\"name\">Name</label>
          <input id=\"name\" name=\"name\" type=\"text\" required placeholder=\"Your name\" autocomplete=\"name\" />
          <button type=\"submit\">Submit</button>
          <div id=\"msg\" class=\"msg\"></div>
        </form>
      </div>
    </div>
    <script>
      const form = document.getElementById('form');
      const nameEl = document.getElementById('name');
      const msg = document.getElementById('msg');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = (nameEl.value || '').trim();
        if (!name) { msg.textContent = 'Please enter your name.'; return; }
        msg.textContent = 'Submitting…';
        try {
          const res = await fetch('/Prod/formular', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
          });
          if (res.ok) { msg.textContent = 'Submitted!'; }
          else { msg.textContent = 'Submission failed (' + res.status + ').'; }
        } catch (err) { msg.textContent = 'Network error.'; }
      });
    </script>
  </body>
</html>"""


def _lower_headers(headers: dict | None) -> dict:
    if not headers:
        return {}
    return {str(k).lower(): v for k, v in headers.items()}


def _extract_ip(event: dict) -> str | None:
    headers = _lower_headers(event.get('headers'))
    xff = headers.get('x-forwarded-for')
    if xff:
        ip = xff.split(',')[0].strip()
        if ip:
            return ip
    try:
        return event.get("requestContext", {}).get("identity", {}).get("sourceIp")
    except Exception:
        return None


_ANDROID_MODEL_RE = re.compile(r"Android [^;\)]*;\s*([^;\)]+)")


def _parse_phone_model(user_agent: str | None) -> str:
    if not user_agent:
        return "Unknown"
    ua = user_agent
    if "iPhone" in ua:
        return "iPhone"
    if "iPad" in ua:
        return "iPad"
    m = _ANDROID_MODEL_RE.search(ua)
    if m:
        model = m.group(1).strip().split(" Build")[0].strip()
        return model
    for brand in ["Pixel", "Nexus", "Huawei", "HUAWEI", "OnePlus", "SM-", "M200", "Redmi", "Mi "]:
        if brand in ua:
            idx = ua.find(brand)
            snippet = ua[idx: idx + 32]
            return snippet.split(";")[0].split(")")[0]
    return "Mobile"


def _read_body(event: dict) -> str:
    body = event.get('body', '')
    if event.get('isBase64Encoded') and body:
        try:
            return base64.b64decode(body).decode('utf-8', errors='replace')
        except Exception:
            return ''
    return body or ''


def lambda_handler(event, context):
    logger.info(event)
    try:
        method = event.get('httpMethod')
        path = event.get('path') or '/'

        # GET / returns HTML
        if method == 'GET' and path == '/':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/html; charset=utf-8',
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                },
                'body': _html_form_page()
            }

        # POST /formular custom handling
        if method == 'POST' and path == '/formular':
            headers = _lower_headers(event.get('headers'))
            body_raw = _read_body(event)
            try:
                payload = json.loads(body_raw) if body_raw else {}
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Invalid JSON'})
                }

            name = (payload.get('name') or '').strip()
            if not name:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Missing "name"'})
                }

            phone_model = _parse_phone_model(headers.get('user-agent'))
            ip = _extract_ip(event) or ''
            queue_url = os.environ['SQS_QUEUE_URL']

            message = {'name': name, 'phoneModel': phone_model, 'ip': ip}
            logger.info("formular_submission %s", json.dumps(message))
            sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'status': 'ok'})
            }

        # Default: record request
        queue_url = os.environ['SQS_QUEUE_URL']
        table_name = os.environ['DYNAMODB_TABLE']
        table = dynamodb.Table(table_name)
        body = _read_body(event)

        request_id = str(uuid.uuid4())
        sqs_message = {
            'requestId': request_id,
            'method': method,
            'path': path,
            'body': body,
            'timestamp': datetime.utcnow().isoformat()
        }
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(sqs_message))
        table.put_item(Item={
            'id': request_id,
            'method': method,
            'path': path,
            'body': body,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'processed'
        })

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Request processed successfully',
                'requestId': request_id,
                'method': method,
                'path': path
            })
        }

    except Exception as e:
        logger.exception("Unhandled error")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
