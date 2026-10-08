# AWS Lambda 速習ガイド 🚀

Python の知識がある人が **AWS Lambda の概念と、Web/API の作り方**を最短で掴むためのガイドです。
各ステップは **ローカルで動くコード** になっていて、AWS アカウントなしで試せます(デプロイは最後のステップ)。

> 📌 これは叩き台です。言語は Python 3.13、IaC は AWS SAM で書いています。

## 🎯 このガイドで分かること

- Lambda が「何を」「いつ」「どう課金して」実行するのか
- event / context / ハンドラ / コールド スタートといった基本概念
- API Gateway(HTTP API)経由で REST API を作る方法
- DynamoDB を使った CRUD、バリデーション、エラー処理、ログ
- ローカルでのテストと、SAM によるデプロイ

## ⚡ まず動かす(AWS 不要)

```bash
python src/step1_hello.py
python src/step4_router.py
python src/step9_sqs_worker.py
python -m unittest discover -s tests -v   # Todo API のテスト (標準ライブラリのみ)
```

必要なのは Python 3.10+ だけです(依存ライブラリなし)。

## 📚 ステップ一覧

| Step | 内容 | ファイル |
|------|------|----------|
| 0 | 概念を理解する | [docs/CONCEPTS.md](docs/CONCEPTS.md) |
| 1 | 最小の Lambda 関数 | [src/step1_hello.py](src/step1_hello.py) |
| 2 | event / context / 環境変数 / コールド スタート | [src/step2_event_context.py](src/step2_event_context.py) |
| 3 | HTTP リクエストを受けてレスポンスを返す | [src/step3_http_response.py](src/step3_http_response.py) |
| 4 | 1 関数でルーティング | [src/step4_router.py](src/step4_router.py) |
| 5 | Todo API(DynamoDB CRUD + バリデーション + ログ) | [src/todo_api/app.py](src/todo_api/app.py) |
| 6 | テスト | [tests/test_handlers.py](tests/test_handlers.py) |
| 7 | デプロイ(SAM) | [docs/DEPLOY.md](docs/DEPLOY.md) / [template.yaml](template.yaml) |
| 8 | S3 トリガー | [src/step8_s3_trigger.py](src/step8_s3_trigger.py) / [docs/EVENT_DRIVEN.md](docs/EVENT_DRIVEN.md) |
| 9 | SQS トリガー(部分バッチ失敗・DLQ) | [src/step9_sqs_worker.py](src/step9_sqs_worker.py) / [template-events.yaml](template-events.yaml) |
| 10 | Cognito + JWT 認証 | [src/step10_jwt_claims.py](src/step10_jwt_claims.py) / [docs/AUTH_COGNITO.md](docs/AUTH_COGNITO.md) / [template-auth.yaml](template-auth.yaml) |
| 11 | CDK(Python)で書く | [docs/CDK.md](docs/CDK.md) / [cdk/](cdk/) |
| + | Web/API 設計の選択肢 | [docs/WEB_API.md](docs/WEB_API.md) |
| + | 参考: Cloudflare Workers / D1 / Pages との比較 | [docs/CLOUDFLARE.md](docs/CLOUDFLARE.md) |

## 🧠 30 秒で分かる Lambda

```
リクエスト → [API Gateway] → [Lambda: handler(event, context)] → [DynamoDB など]
                              ↑ サーバー管理不要・リクエスト数と実行時間で課金・使われなければ 0 円
```

```python
def handler(event, context):      # これが Lambda のすべて
    return {"statusCode": 200, "body": "ok"}
```

## 🔁 Python の Web フレームワークとの違い

| 観点 | Flask / FastAPI | Lambda |
|------|-----------------|--------|
| 起動 | プロセスが常駐して待ち受ける | リクエストごとに実行環境が起動/再利用される |
| ポート・サーバー | 自分で面倒を見る | なし(API Gateway が受ける) |
| スケール | 台数/プロセス数を設計 | 同時実行数に応じて自動 |
| 状態 | メモリに持てる | **持たない前提**(DB/S3 に置く) |
| 課金 | 稼働時間 | 呼び出し回数 × 実行時間 × メモリ |
| ルーティング | フレームワーク | API Gateway か関数内の dict |
| ローカル実行 | `uvicorn` | 関数をただ呼ぶ / `sam local` |

## 🧭 学習の進め方

1. [docs/CONCEPTS.md](docs/CONCEPTS.md) を読む(10 分)
2. Step 1〜4 を順に実行し、コードを書き換えて挙動を見る
3. Step 5 の Todo API とテストを読む
4. AWS アカウントがあれば [docs/DEPLOY.md](docs/DEPLOY.md) でデプロイ
5. Step 8〜11 で S3/SQS、認証、CDK へ広げる

## ✅ 検証状況

- Step 1〜4、8〜10 と `tests/`(14 件)は Python 3.13 でローカル実行を確認済み
- `template*.yaml`、`cdk/`、デプロイ手順は **未デプロイ・未合成**(実 AWS / SAM / CDK では未検証)。初回は `sam validate --lint` / `cdk synth` から始めてください

## 🔗 参考

- [AWS Lambda 開発者ガイド](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [AWS SAM 開発者ガイド](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [AWS Lambda Powertools for Python](https://docs.powertools.aws.dev/lambda/python/latest/)(本格運用時のログ/トレース/バリデーション)
