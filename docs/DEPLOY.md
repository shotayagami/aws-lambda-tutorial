# Step 7: デプロイ(AWS SAM)

> ⚠️ この手順は **実 AWS では未検証** です。課金が発生し得るので、試した後は必ず削除してください。

## 準備

1. AWS アカウントと、操作用の認証情報(推奨: IAM Identity Center / `aws configure sso`)
2. [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) と [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
3. 確認:

```bash
aws sts get-caller-identity
sam --version
```

## 手順

```bash
sam validate --lint          # テンプレートの検証
sam build                    # src/ をビルド (.aws-sam/ に出力)
sam deploy --guided          # 初回のみ対話式。以後は sam deploy
```

`--guided` で聞かれること:
- Stack Name(例: `lambda-todo`)、Region(例: `ap-northeast-1`)
- `Save arguments to samconfig.toml` は Yes にすると次回から対話不要

完了すると Outputs に `ApiUrl` が出ます。

```bash
API=https://xxxx.execute-api.ap-northeast-1.amazonaws.com/todos

curl -X POST $API -H "content-type: application/json" -d '{"title":"first"}'
curl $API
curl -X PUT  $API/<id> -H "content-type: application/json" -d '{"done":true}'
curl -X DELETE $API/<id>
```

## ログを見る

```bash
sam logs --stack-name lambda-todo --tail
```

## ローカルで API を起動(Docker が必要)

```bash
sam local start-api
```

DynamoDB はローカルに無いので、`TABLE_NAME` 指定と実テーブル or DynamoDB Local が別途必要です。
まずは `python -m unittest` のテストで十分に確認し、結合は実環境で行うのが手軽です。

## 後片付け(重要)

```bash
sam delete --stack-name lambda-todo
```

DynamoDB テーブル・API・関数・ロールがまとめて削除されます。

## ほかのデプロイ方法

| 方法 | 用途 |
|------|------|
| マネジメント コンソール | 最初の体験。関数を直接貼り付けて Test 実行 |
| zip + `aws lambda update-function-code` | 単純な関数の更新 |
| CDK / Terraform / Serverless Framework | チームで標準化済みの IaC がある場合 |
| コンテナ イメージ | 10GB までの大きな依存(ML ライブラリなど) |
