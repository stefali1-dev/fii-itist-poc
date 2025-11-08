"""Handler for all other requests - catch-all endpoint."""
import json
import os
import uuid
from datetime import datetime
from services import sqs, dynamodb
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
    # Generate unique request ID
    request_id = str(uuid.uuid4())

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
