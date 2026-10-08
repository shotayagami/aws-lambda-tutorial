"""標準ライブラリだけで動くテスト:  python -m unittest discover -s tests -v

AWS には一切接続しない。event を自作して handler を直接呼ぶだけ。
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from _fake import FakeContext, http_event  # noqa: E402
from todo_api import app  # noqa: E402


class FakeTable:
    """DynamoDB Table のうち使う 4 メソッドだけを模したインメモリ実装。"""

    def __init__(self):
        self.items = {}

    def put_item(self, Item):
        self.items[Item["id"]] = dict(Item)

    def get_item(self, Key):
        item = self.items.get(Key["id"])
        return {"Item": dict(item)} if item else {}

    def delete_item(self, Key):
        self.items.pop(Key["id"], None)

    def scan(self):
        return {"Items": [dict(i) for i in self.items.values()]}


def call(method, route, **kw):
    res = app.handler(http_event(method, route, **kw), FakeContext())
    body = json.loads(res["body"]) if res["body"] else None
    return res["statusCode"], body


class TodoApiTest(unittest.TestCase):
    def setUp(self):
        app._table = FakeTable()  # DynamoDB の代わりに差し替え

    def test_create_and_get(self):
        status, todo = call("POST", "/todos", body={"title": "buy milk"})
        self.assertEqual(status, 201)
        status, got = call("GET", "/todos/{id}", path_params={"id": todo["id"]})
        self.assertEqual((status, got["title"]), (200, "buy milk"))

    def test_list(self):
        call("POST", "/todos", body={"title": "a"})
        status, items = call("GET", "/todos")
        self.assertEqual((status, len(items)), (200, 1))

    def test_validation(self):
        self.assertEqual(call("POST", "/todos", body={"title": ""})[0], 422)
        self.assertEqual(call("POST", "/todos", body={})[0], 422)

    def test_invalid_json(self):
        event = http_event("POST", "/todos")
        event["body"] = "{oops"
        self.assertEqual(app.handler(event, FakeContext())["statusCode"], 400)

    def test_update_and_delete(self):
        _, todo = call("POST", "/todos", body={"title": "a"})
        pid = {"id": todo["id"]}
        status, updated = call("PUT", "/todos/{id}", path_params=pid, body={"done": True})
        self.assertEqual((status, updated["done"]), (200, True))
        self.assertEqual(call("DELETE", "/todos/{id}", path_params=pid)[0], 204)
        self.assertEqual(call("GET", "/todos/{id}", path_params=pid)[0], 404)

    def test_unknown_route(self):
        self.assertEqual(call("GET", "/nope")[0], 404)

    def test_unexpected_error_is_500(self):
        app._table = None
        os.environ.pop("TABLE_NAME", None)  # KeyError -> 500 になること
        self.assertEqual(call("GET", "/todos")[0], 500)


if __name__ == "__main__":
    unittest.main()
