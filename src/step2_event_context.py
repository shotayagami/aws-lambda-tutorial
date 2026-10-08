"""Step 2: event / context / 実行環境の再利用

- event  : 呼び出し元が渡す JSON (dict)。形はトリガーごとに違う
- context: 関数名・メモリ・残り時間・リクエストIDなど実行時情報
- グローバル領域はコールド スタート時に1回だけ実行され、
  ウォーム (再利用) 状態の呼び出しでは使い回される

    python src/step2_event_context.py
"""
import os

from _fake import FakeContext

# ---- Init フェーズ: コールド スタート時のみ実行される ----
# DB クライアントの生成や設定読み込みはここに置く (毎回作らない)
INVOCATION_COUNT = 0
GREETING = os.environ.get("GREETING", "Hello")  # 環境変数で設定を外から渡す


def handler(event, context):
    global INVOCATION_COUNT
    INVOCATION_COUNT += 1  # ウォームなら増え続ける / コールドなら 1 に戻る

    return {
        "greeting": GREETING,
        "request_id": context.aws_request_id,
        "function": context.function_name,
        "memory_mb": context.memory_limit_in_mb,
        "remaining_ms": context.get_remaining_time_in_millis(),
        "invocation_count_in_this_container": INVOCATION_COUNT,
    }


if __name__ == "__main__":
    for _ in range(3):  # 同じプロセス内で 3 回 = ウォーム再利用の疑似体験
        print(handler({}, FakeContext()))
