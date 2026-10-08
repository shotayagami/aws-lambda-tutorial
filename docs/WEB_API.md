# Web / API を作るときの選択肢

## 1. Lambda を HTTP に公開する 3 つの方法

| 方式 | 特徴 | 向き |
|------|------|------|
| **Function URL** | 関数に直接 HTTPS の URL を付ける。設定が最小 | 試作、Webhook 受け口 |
| **API Gateway HTTP API** | 安価・低レイテンシ。JWT 認可、CORS 設定、ルート定義 | **新規の API 全般(このガイドの既定)** |
| **API Gateway REST API** | 高機能(使用量プラン、API キー、リクエスト検証、WAF 連携など) | それらが必要な場合 |

## 2. HTTP API の event(payload format 2.0)

```json
{
  "version": "2.0",
  "routeKey": "GET /todos/{id}",
  "rawPath": "/todos/abc",
  "rawQueryString": "a=1",
  "headers": {"content-type": "application/json"},
  "queryStringParameters": {"a": "1"},
  "pathParameters": {"id": "abc"},
  "requestContext": {"http": {"method": "GET", "path": "/todos/abc"}},
  "body": "{\"x\":1}",
  "isBase64Encoded": false
}
```

ハマりどころ:
- `queryStringParameters` / `pathParameters` / `body` は**無いとキー自体が無い or None**。`.get(...) or {}` で受ける
- `headers` のキーは**小文字**に正規化される
- `body` は文字列。バイナリは `isBase64Encoded: true` で base64

## 3. レスポンスの形

```python
{"statusCode": 200, "headers": {"content-type": "application/json"}, "body": "<文字列>"}
```

- `body` に dict を入れない(`json.dumps`)
- HTTP API は dict だけ返すと自動で JSON 化もされるが、**ステータスやヘッダーを明示する書き方を基本**にする
- 204 のときは body を空に

## 4. ルーティング設計

| パターン | 内容 | 長所 / 短所 |
|----------|------|-------------|
| **Lambdalith**(Step 4/5) | 1 関数 + `ANY` で全ルートを受け、関数内で振り分け | 管理が楽、コールド スタートが共有される / 権限・サイズが大きくなりがち |
| **関数 per ルート** | ルートごとに関数を分ける | 権限を最小化しやすい / 関数数・IaC が増える |

最初は Lambdalith で十分です。権限や性能の要件が分かれてきたら分割します。

## 5. 認証・認可

- **JWT オーソライザー**(HTTP API): Cognito / Auth0 / Entra ID などの JWT を API Gateway が検証。関数側は `requestContext.authorizer.jwt.claims` を読むだけ
- **Lambda オーソライザー**: 独自ロジックで許可/拒否
- **IAM 認可**: サービス間呼び出し向け
- 認可(「そのユーザーにそのデータを触らせてよいか」)は**必ず関数側でも確認**する

## 6. CORS

ブラウザの SPA から呼ぶ場合は必要。HTTP API なら SAM で宣言できます:

```yaml
Resources:
  HttpApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      CorsConfiguration:
        AllowOrigins: ["https://example.com"]
        AllowMethods: ["GET", "POST", "PUT", "DELETE"]
        AllowHeaders: ["content-type", "authorization"]
```

(この場合、各関数の `Events` に `ApiId: !Ref HttpApi` を指定します)

## 7. 既存フレームワークを使いたい場合

- **Powertools for AWS Lambda (Python)**: `APIGatewayHttpResolver` で Flask 風のルーティング + 検証 + ログ/トレース
- **Mangum**: FastAPI / Starlette を Lambda 上で動かすアダプタ
- **AWS Lambda Web Adapter**: 任意の Web フレームワーク(Flask 等)をほぼそのまま載せる

小さな API はこのガイドの素朴な書き方、チーム開発や既存資産があるなら上記を検討。

## 8. DB の選び方(簡易)

| 用途 | 候補 |
|------|------|
| キー検索中心、運用ゼロ | **DynamoDB**(接続管理が不要で Lambda と相性が良い) |
| リレーショナル | Aurora / RDS。**RDS Proxy** で接続数を抑える |
| ファイル | S3(署名付き URL でクライアントと直接やり取り) |

## 9. 本番前チェックリスト

- [ ] タイムアウトとメモリを実測で決めた
- [ ] 実行ロールは最小権限
- [ ] 想定外エラーは 500 + ログ、内部情報は返さない
- [ ] 入力バリデーションがある
- [ ] CloudWatch Logs の保持期間を設定(既定は無期限)
- [ ] 非同期系は冪等で、DLQ / 送信先を設定
- [ ] 同時実行数の上限が下流(DB 等)を壊さない
