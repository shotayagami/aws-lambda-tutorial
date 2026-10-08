"""Step 10: JWT 認証 (Cognito) を使った API

HTTP API の JWT オーソライザーが、トークンの署名・有効期限・issuer・audience を
Lambda の *前段* で検証する。検証に通ったときだけ関数が呼ばれ、
クレームは event["requestContext"]["authorizer"]["jwt"] に入って届く。

関数側の責務:
  1. 認証 (誰か)  : claims["sub"] を読む。トークンの検証自体は API Gateway 任せ
  2. 認可 (何を許すか): scope の確認、そして *他人のデータに触らせない* こと
     例) ユーザーごとにデータを分けるキー (owner = sub) を必ず条件に入れる

注意: 関数を API Gateway 経由以外 (Function URL 等) でも公開すると、この前提が崩れる。

    python src/step10_jwt_claims.py
"""
import json

from _fake import FakeContext, http_event

NOTES = {  # 学習用のインメモリ データ。{owner(sub): [notes]}
    "user-a": ["a のメモ 1"],
    "user-b": ["b のメモ 1"],
}


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def get_jwt(event):
    return (event.get("requestContext", {}).get("authorizer") or {}).get("jwt")


def handler(event, context):
    jwt = get_jwt(event)
    if not jwt:  # オーソライザーが付いていない/設定ミス -> 安全側に倒して拒否
        return response(401, {"error": "unauthorized"})

    claims = jwt["claims"]
    scopes = jwt.get("scopes") or []

    if "notes/read" not in scopes:  # スコープ (アクセス トークンの場合) の確認
        return response(403, {"error": "missing scope: notes/read"})

    owner = claims["sub"]  # 自分のデータだけを返す。URL やボディで owner を受け取らない
    return response(200, {"owner": owner, "notes": NOTES.get(owner, [])})


def with_jwt(event, sub, scopes=()):
    """学習用: オーソライザー通過後の event を再現する。"""
    event["requestContext"]["authorizer"] = {
        "jwt": {"claims": {"sub": sub}, "scopes": list(scopes)}
    }
    return event


if __name__ == "__main__":
    ctx = FakeContext()
    print(handler(http_event("GET", "/notes"), ctx))  # 認証なし -> 401
    print(handler(with_jwt(http_event("GET", "/notes"), "user-a"), ctx))  # scope 不足 -> 403
    print(handler(with_jwt(http_event("GET", "/notes"), "user-a", ["notes/read"]), ctx))
    print(handler(with_jwt(http_event("GET", "/notes"), "user-b", ["notes/read"]), ctx))
