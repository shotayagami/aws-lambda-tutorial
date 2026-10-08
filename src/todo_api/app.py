"""Step 5: デプロイ可能な Todo API (DynamoDB + バリデーション + 構造化ログ)

    GET    /todos          一覧
    POST   /todos          作成   {"title": "..."}
    GET    /todos/{id}     取得
    PUT    /todos/{id}     更新   {"title": "...", "done": true}
    DELETE /todos/{id}     削除

テーブルは get_table() から取得する。テストでは差し替え可能 (tests/ 参照)。
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Lambda ではルート ロガーに出すと CloudWatch Logs へ流れる

_table = None  # 初回利用時に作る → ウォーム状態の呼び出しでは再利用される


def get_table():
    global _table
    if _table is None:
        import boto3  # Lambda の Python ランタイムには同梱済み

        _table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table


class HttpError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def response(status, body=None):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False) if body is not None else "",
    }


def read_json(event):
    try:
        data = json.loads(event.get("body") or "")
    except json.JSONDecodeError:
        raise HttpError(400, "invalid JSON")
    if not isinstance(data, dict):
        raise HttpError(400, "body must be a JSON object")
    return data


def validate_title(data):
    title = data.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 100:
        raise HttpError(422, "title is required (1-100 chars)")
    return title.strip()


# ---- ハンドラ ----
def list_todos(event):
    # scan は学習用。データが増えたら Query + インデックス設計に切り替える
    return response(200, get_table().scan().get("Items", []))


def create_todo(event):
    title = validate_title(read_json(event))
    item = {
        "id": str(uuid.uuid4()),
        "title": title,
        "done": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    get_table().put_item(Item=item)
    return response(201, item)


def get_todo(event):
    item = get_table().get_item(Key={"id": event["pathParameters"]["id"]}).get("Item")
    if not item:
        raise HttpError(404, "not found")
    return response(200, item)


def update_todo(event):
    todo_id = event["pathParameters"]["id"]
    item = get_table().get_item(Key={"id": todo_id}).get("Item")
    if not item:
        raise HttpError(404, "not found")
    data = read_json(event)
    if "title" in data:
        item["title"] = validate_title(data)
    if "done" in data:
        if not isinstance(data["done"], bool):
            raise HttpError(422, "done must be boolean")
        item["done"] = data["done"]
    get_table().put_item(Item=item)
    return response(200, item)


def delete_todo(event):
    get_table().delete_item(Key={"id": event["pathParameters"]["id"]})
    return response(204)


ROUTES = {
    "GET /todos": list_todos,
    "POST /todos": create_todo,
    "GET /todos/{id}": get_todo,
    "PUT /todos/{id}": update_todo,
    "DELETE /todos/{id}": delete_todo,
}


def handler(event, context):
    route_key = event.get("routeKey")
    try:
        route = ROUTES.get(route_key)
        if route is None:
            raise HttpError(404, f"no route: {route_key}")
        result = route(event)
    except HttpError as e:  # 想定内のエラー -> 4xx
        result = response(e.status, {"error": e.message})
    except Exception:  # 想定外 -> 500。詳細はログにだけ出し、利用者には漏らさない
        logger.exception("unhandled error")
        result = response(500, {"error": "internal server error"})

    # 構造化ログ (JSON 1 行) は CloudWatch Logs Insights で検索しやすい
    logger.info(json.dumps({
        "route": route_key,
        "status": result["statusCode"],
        "request_id": getattr(context, "aws_request_id", None),
    }))
    return result
