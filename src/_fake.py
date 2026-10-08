"""学習用: ローカル実行のためのダミー event / context。

本物の Lambda では AWS が event と context を渡してくる。
ここではそれを手元で再現するだけ。
"""
import time


class FakeContext:
    function_name = "local-function"
    function_version = "$LATEST"
    memory_limit_in_mb = 128
    aws_request_id = "00000000-0000-0000-0000-000000000000"
    invoked_function_arn = "arn:aws:lambda:ap-northeast-1:123456789012:function:local-function"

    def __init__(self, timeout_sec=3):
        self._deadline = time.time() + timeout_sec

    def get_remaining_time_in_millis(self):
        return max(0, int((self._deadline - time.time()) * 1000))


def http_event(method="GET", path="/", query=None, body=None, path_params=None, headers=None):
    """API Gateway HTTP API (payload format 2.0) / Function URL 形式の event を作る。"""
    import json

    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "&".join(f"{k}={v}" for k, v in (query or {}).items()),
        "headers": {"content-type": "application/json", **(headers or {})},
        "queryStringParameters": query,
        "pathParameters": path_params,
        "requestContext": {"http": {"method": method, "path": path}},
        "body": json.dumps(body) if body is not None else None,
        "isBase64Encoded": False,
    }
