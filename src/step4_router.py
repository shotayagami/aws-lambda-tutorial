"""Step 4: 1 つの関数でルーティングする (いわゆる "Lambdalith")

HTTP API の event には routeKey ("GET /items/{id}") が入っている。
SAM / API Gateway 側で "ANY /{proxy+}" をこの関数に向けておけば、
ルーティングは関数内の dict 1 つで足りる。

    python src/step4_router.py
"""
from _fake import FakeContext, http_event
from step3_http_response import response

ITEMS = {"1": {"id": "1", "name": "apple"}}  # デモ用 (本番では DB を使う)


def list_items(event):
    return response(200, list(ITEMS.values()))


def get_item(event):
    item = ITEMS.get(event["pathParameters"]["id"])
    return response(200, item) if item else response(404, {"error": "not found"})


ROUTES = {
    "GET /items": list_items,
    "GET /items/{id}": get_item,
}


def handler(event, context):
    route = ROUTES.get(event["routeKey"])
    if route is None:
        return response(404, {"error": f"no route: {event['routeKey']}"})
    return route(event)


if __name__ == "__main__":
    ctx = FakeContext()
    print(handler(http_event("GET", "/items"), ctx))
    print(handler(http_event("GET", "/items/{id}", path_params={"id": "1"}), ctx))
    print(handler(http_event("GET", "/items/{id}", path_params={"id": "9"}), ctx))
    print(handler(http_event("GET", "/nothing"), ctx))
