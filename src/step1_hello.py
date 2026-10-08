"""Step 1: 最小の Lambda 関数

Lambda の正体は「event と context を受け取る関数」1つだけ。
AWS 側の設定 (Handler = "step1_hello.handler") でこの関数を指す。

Python の関数をそのまま呼ぶだけなので、ローカルでも普通に動く:
    python src/step1_hello.py
"""
from _fake import FakeContext


def handler(event, context):
    name = event.get("name", "world")
    return {"message": f"Hello, {name}!"}


if __name__ == "__main__":
    print(handler({"name": "Lambda"}, FakeContext()))
