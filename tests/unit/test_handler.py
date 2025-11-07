from hello_world import app


def test_root_get_returns_html():
    event = {
        "resource": "/",
        "path": "/",
        "httpMethod": "GET",
        "headers": {
            "Accept": "text/html",
            "Host": "example.execute-api.us-east-1.amazonaws.com",
        },
        "requestContext": {
            "stage": "Prod",
            "resourcePath": "/",
            "httpMethod": "GET",
        },
        "queryStringParameters": None,
        "pathParameters": None,
        "body": None,
        "isBase64Encoded": False,
    }

    ret = app.lambda_handler(event, None)
    assert ret["statusCode"] == 200
    assert "text/html" in ret["headers"].get("Content-Type", "")
    assert "<form" in ret["body"]
    assert "name\"" in ret["body"]
