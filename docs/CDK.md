# CDK (Python) で Lambda を書く

コード: [cdk/](../cdk/) (Todo API を SAM と同じ構成で記述)

## SAM と CDK の違い

| | SAM | CDK |
|---|-----|-----|
| 記述 | YAML(CloudFormation 拡張) | Python / TypeScript などのコード |
| 向き | Lambda 中心の小〜中規模、ローカル実行(`sam local`) | 構成が大きい、ループ/条件/共通部品化したい |
| 権限 | `Policies:` に SAM ポリシー テンプレート | `table.grant_read_write_data(fn)` |
| 出力 | CloudFormation | CloudFormation(`cdk synth` で確認) |
| 学習コスト | 低 | やや高い(construct の概念) |

迷ったら **まず SAM、構成が膨らんだら CDK**。同じ CloudFormation にデプロイされるので、移行も可能です。

## 手順

```bash
npm install -g aws-cdk            # CDK CLI (Node.js が必要)
cd cdk
python -m venv .venv && .venv\Scripts\activate    # Windows。macOS/Linux は source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap                     # アカウント/リージョンごとに 1 回
cdk synth                         # テンプレートを生成して確認
cdk deploy
cdk destroy                       # 後片付け
```

`cdk.json` の `app` は `python3 app.py` です。Windows で `python3` が無い場合は `python app.py` に変更してください。

## コードの見どころ ([cdk/todo_stack.py](../cdk/todo_stack.py))

- `grant_read_write_data` が **最小権限の IAM ポリシー**を自動生成する
- `HttpLambdaIntegration` でルートと関数を結ぶ(API Gateway の Lambda 権限も自動設定)
- `RemovalPolicy.DESTROY` は学習用。**本番のテーブルは RETAIN** を検討する
- `Code.from_asset("../src")` は `src/` をそのまま zip 化する(依存パッケージがある場合は別途ビルドが必要)

## 注意

- API Gateway v2(HTTP API)は `aws-cdk-lib` の安定版に含まれます(以前の `-alpha` 版は不要)
- JWT 認証を足す場合は `aws_cdk.aws_apigatewayv2_authorizers` を使います(バージョンにより API が異なるため公式ドキュメントで確認してください)
- この CDK コードは **`cdk synth` も実行しておらず未検証** です。最初に `cdk synth` で確認してください
