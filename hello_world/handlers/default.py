"""Handler for all other requests - catch-all endpoint."""
import json
import os
import uuid
from datetime import datetime
from aws_clients import sqs, dynamodb
from utils import read_body


def handle_default(event: dict, context) -> dict:
    """
    Handle all other requests (catch-all).
    
    Records the request to both SQS and DynamoDB:
    - Generates unique request ID
    - Sends message to SQS queue
    - Stores request details in DynamoDB
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with request details
    """
    method = event.get('httpMethod')
    path = event.get('path') or '/'
    body = read_body(event)
    
    # Get AWS resources
    queue_url = os.environ['SQS_QUEUE_URL']
    table_name = os.environ['DYNAMODB_TABLE']
    table = dynamodb.Table(table_name)
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Prepare message
    sqs_message = {
        'requestId': request_id,
        'method': method,
        'path': path,
        'body': body,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Send to SQS
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(sqs_message))
    
    # Store in DynamoDB
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
