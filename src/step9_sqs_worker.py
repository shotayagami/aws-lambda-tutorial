"""Step 9: SQS トリガー (キューのメッセージをバッチで処理する)

Lambda 側がキューをポーリングし、最大 BatchSize 件を 1 回の呼び出しにまとめて渡す。

重要:
  - 例外を投げると *バッチ全体* が失敗し、成功済みのメッセージも再配信される
  - 失敗したメッセージだけ返すには「部分バッチ レスポンス」を使う
      template で  FunctionResponseTypes: [ReportBatchItemFailures]  を指定し、
      戻り値で {"batchItemFailures": [{"itemIdentifier": messageId}, ...]} を返す
  - SQS は少なくとも 1 回配信 -> 同じメッセージが重複して届き得る。冪等に作る
  - 何度も失敗するメッセージは DLQ (デッドレター キュー) に退避する (maxReceiveCount)
  - キューの VisibilityTimeout は関数の Timeout より十分長く (目安: 6 倍以上)

    python src/step9_sqs_worker.py
"""
import json

from _fake import FakeContext

_done_ids = set()  # 学習用の冪等性チェック。本番は DynamoDB の条件付き書き込みなどで行う


def process(message_body):
    if "amount" not in message_body:
        raise ValueError("amount is required")
    return message_body["amount"] * 2


def handler(event, context):
    failures = []
    for record in event["Records"]:
        message_id = record["messageId"]
        try:
            if message_id in _done_ids:  # 重複配信は何もせず成功扱い
                continue
            process(json.loads(record["body"]))
            _done_ids.add(message_id)
        except Exception as e:
            print(json.dumps({"level": "ERROR", "message_id": message_id, "error": str(e)}))
            failures.append({"itemIdentifier": message_id})  # このメッセージだけ再試行させる

    return {"batchItemFailures": failures}


def sqs_event(*bodies):
    """学習用: SQS event を作る。"""
    return {
        "Records": [
            {
                "messageId": f"msg-{i}",
                "body": body if isinstance(body, str) else json.dumps(body),
                "eventSource": "aws:sqs",
            }
            for i, body in enumerate(bodies)
        ]
    }


if __name__ == "__main__":
    event = sqs_event({"amount": 1}, {"oops": True}, "not json", {"amount": 3})
    print(handler(event, FakeContext()))  # msg-1 と msg-2 だけが失敗として返る
