"""Handler for POST /form - processes form submissions."""
import json
import os
from aws_clients import sqs, logger
from utils import lower_headers, extract_ip, read_body, parse_phone_model


def handle_form(event: dict, context) -> dict:
    """
    Handle POST /form requests.
    
    Processes form submission:
    - Validates name field
    - Extracts phone model from User-Agent
    - Extracts client IP
    - Sends message to SQS queue
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with status and JSON body
    """
    headers = lower_headers(event.get('headers'))
    body_raw = read_body(event)
    
    # Parse JSON body
    try:
        payload = json.loads(body_raw) if body_raw else {}
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid JSON'})
        }
    
    # Validate required field
    name = (payload.get('name') or '').strip()
    if not name:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing "name"'})
        }
    
    # Extract metadata
    phone_model = parse_phone_model(headers.get('user-agent'))
    ip = extract_ip(event) or ''
    queue_url = os.environ['SQS_QUEUE_URL']
    
    # Prepare and send message
    message = {
        'name': name,
        'phoneModel': phone_model,
        'ip': ip
    }
    logger.info("form_submission %s", json.dumps(message))
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'status': 'ok'})
    }
