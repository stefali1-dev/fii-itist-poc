"""Main Lambda handler - routes requests to appropriate handlers."""
import json
from services import logger
from handlers import handle_home, handle_formular, handle_results, handle_default


def lambda_handler(event, context):
    """
    Main Lambda handler - routes requests to appropriate handlers.
    
    Routes:
    - GET /       -> handle_home (HTML form)
    - POST /formular -> handle_formular (form submission)
    - GET /results -> handle_results (participants display page)
    - *           -> handle_default (catch-all)
    """
    logger.info(event)
    
    try:
        method = event.get('httpMethod')
        path = event.get('path') or '/'
        
        # Route to appropriate handler
        if method == 'GET' and path == '/':
            return handle_home(event, context)
        
        if method == 'POST' and path == '/formular':
            return handle_formular(event, context)
        
        if method == 'GET' and path == '/results':
            return handle_results(event, context)
        
        # Catch-all for all other requests
        return handle_default(event, context)
    
    except Exception as e:
        logger.exception("Unhandled error in lambda_handler")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
