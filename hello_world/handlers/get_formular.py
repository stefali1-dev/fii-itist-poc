from services import sqs, logger, dynamodb
import os
import json
from utils import censor_en_ro

def handle_get_formular(event: dict, context) -> dict:
    
    table_name = os.environ['DYNAMODB_TABLE']
    table = dynamodb.Table(table_name)
    
    all_items = []
    scan_kwargs = {}

    while True:
        response = table.scan(**scan_kwargs)
        all_items.extend(response.get('Items', []))

        # Check if there are more items to scan
        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break

        scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

    # Return everything as JSON (Lambda proxy integration style)
    
    names = [item["name"] for item in all_items]
    
    names_censored = [censor_en_ro(name) for name in names]
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "participants": names_censored
        })
    }