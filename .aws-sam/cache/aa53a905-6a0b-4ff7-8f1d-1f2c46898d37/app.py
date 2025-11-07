import json
import os
import boto3
import uuid
from datetime import datetime

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # Get environment variables
        queue_url = os.environ['SQS_QUEUE_URL']
        table_name = os.environ['DYNAMODB_TABLE']
        table = dynamodb.Table(table_name)
        
        # Extract request info
        method = event['httpMethod']
        path = event['path']
        body = event.get('body', '')
        
        # Generate unique ID
        request_id = str(uuid.uuid4())
        
        # Send task to SQS
        sqs_message = {
            'requestId': request_id,
            'method': method,
            'path': path,
            'body': body,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(sqs_message)
        )
        
        # Write to DynamoDB
        table.put_item(
            Item={
                'id': request_id,
                'method': method,
                'path': path,
                'body': body,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'processed'
            }
        )
        
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
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e)
            })
        }
