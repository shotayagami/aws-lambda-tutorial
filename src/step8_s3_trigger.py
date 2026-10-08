"""Step 8: S3 トリガー (オブジェクト作成イベントを受けて処理する)

S3 にファイルが置かれると、Lambda が *非同期* に呼ばれる (失敗時は自動リトライ)。
1 つの event に Records が複数入ることがある。

落とし穴:
  - オブジェクト キーは URL エンコードされて届く (スペースは "+")。unquote_plus で戻す
  - 同じバケットに書き戻すと自分自身をトリガーして無限ループする
    -> 出力先は別バケット、または prefix / suffix フィルタで入力側だけに絞る
  - 非同期はリトライされ得る -> 同じファイルを 2 回処理しても壊れない (冪等) 作りにする

    python src/step8_s3_trigger.py
"""
from urllib.parse import unquote_plus

from _fake import FakeContext

_s3 = None


def get_s3():
    global _s3
    if _s3 is None:
        import boto3

        _s3 = boto3.client("s3")
    return _s3


def s3_event(bucket, key, size=0, event_name="ObjectCreated:Put"):
    """学習用: S3 通知 event を作る (キーは本物と同じく URL エンコード済みで渡す)。"""
    return {
        "Records": [{
            "eventSource": "aws:s3",
            "eventName": event_name,
            "s3": {"bucket": {"name": bucket}, "object": {"key": key, "size": size}},
        }]
    }


def handler(event, context):
    processed = []
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        if not key.lower().endswith(".txt"):  # フィルタは SAM の Filter でも指定できるが、念のため
            continue

        body = get_s3().get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        processed.append({"key": key, "chars": len(body)})

    return {"processed": processed}


class FakeS3:
    """get_object だけを模したダミー。"""

    def __init__(self, files):
        self.files = files

    def get_object(self, Bucket, Key):
        import io

        return {"Body": io.BytesIO(self.files[(Bucket, Key)].encode("utf-8"))}


if __name__ == "__main__":
    _s3 = FakeS3({("demo-bucket", "my notes/今日 のメモ.txt"): "こんにちは Lambda"})
    # "my notes/今日 のメモ.txt" は実際には "my+notes/%E4%BB%8A..." のように届く
    from urllib.parse import quote_plus

    key = quote_plus("my notes/今日 のメモ.txt", safe="/")
    print(key)
    print(handler(s3_event("demo-bucket", key), FakeContext()))
    print(handler(s3_event("demo-bucket", "image.png"), FakeContext()))
