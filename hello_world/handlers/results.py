"""Handler for GET /results - displays the participants wall page."""
import os


def handle_results(event: dict, context) -> dict:
    """
    Handle GET /results requests.
    
    Returns the HTML results page that displays all participants
    in a dynamic "wall of fame" style.
    """
    # Read the HTML template
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'results.html')
    with open(template_path, 'r') as f:
        html_content = f.read()
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html; charset=utf-8',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        },
        'body': html_content
    }
