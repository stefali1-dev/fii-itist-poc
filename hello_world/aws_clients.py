"""Shared AWS service clients (singleton pattern)."""
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global clients - initialized once per Lambda container
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
