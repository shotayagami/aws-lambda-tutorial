"""Step 3: Web リクエストを受けてレスポンスを返す

API Gateway (HTTP API) / Function URL 経由だと event は HTTP リクエストの表現になる。
戻り値は次の形の dict にすると HTTP レスポンスとして返される:

    {"statusCode": 200, "headers": {...}, "body": "文字列"}

注意: body は必ず「文字列」。dict のまま返さない (json.dumps する)。

    python src/step3_http_response.py
"""
import base64
import json

from _fake import FakeContext, http_event


def response(status, body, headers=None):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json", **(headers or {})},
        "body": json.dumps(body, ensure_ascii=False),
    }


def parse_json_body(event):
    raw = event.get("body")
    if raw is None:
        return None
    if event.get("isBase64Encoded"):  # バイナリや一部設定では base64 で来る
        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw)


def handler(event, context):
    method = event["requestContext"]["http"]["method"]
    query = event.get("queryStringParameters") or {}  # 無いと None になる点に注意

    if method == "GET":
        return response(200, {"hello": query.get("name", "world")})

    if method == "POST":
        try:
            data = parse_json_body(event)
        except json.JSONDecodeError:
            return response(400, {"error": "invalid JSON"})
        return response(201, {"received": data})

    return response(405, {"error": "method not allowed"})


if __name__ == "__main__":
    ctx = FakeContext()
    print(handler(http_event("GET", "/hello", query={"name": "Taro"}), ctx))
    print(handler(http_event("POST", "/hello", body={"a": 1}), ctx))
    print(handler(http_event("DELETE", "/hello"), ctx))
