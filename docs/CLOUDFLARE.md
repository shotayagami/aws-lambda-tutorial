# 参考: Cloudflare Workers / D1 / Pages との比較

AWS Lambda で学んだ概念を、Cloudflare の同種サービスに対応づけるための早見表です。
**数値・制限・料金は変わりやすいので、採用判断の前に必ず公式ドキュメントで確認してください。**

## 1. サービス対応表

| やりたいこと | AWS | Cloudflare |
|--------------|-----|-----------|
| 関数の実行 | Lambda | **Workers** |
| HTTP の入口 | API Gateway / Function URL | Workers 自体が入口(ルート/カスタムドメインを割り当てるだけ) |
| 静的サイト・フロント配信 | S3 + CloudFront / Amplify | **Pages**(または Workers の静的アセット) |
| RDB | RDS / Aurora | **D1**(SQLite ベース) |
| KV / NoSQL | DynamoDB | Workers KV / Durable Objects |
| オブジェクトストレージ | S3 | R2(S3 互換 API) |
| キュー | SQS | Queues |
| 定期実行 | EventBridge Scheduler | Cron Triggers |
| 認証 | Cognito | Access / 自前 JWT 検証 など |
| IaC / CLI | SAM / CDK | **Wrangler**(`wrangler.toml` / `wrangler.jsonc`) |

## 2. 実行モデルの違い(最重要)

| 観点 | Lambda | Workers |
|------|--------|---------|
| 実行単位 | microVM 上のコンテナ的な実行環境 | **V8 isolate**(軽量な分離環境) |
| コールド スタート | 数百 ms 程度(言語・サイズ・VPC で伸びる) | 非常に小さい(数 ms 程度とされる) |
| 同時実行 | 1 環境 = 同時 1 リクエスト。増えると環境が増える | 1 isolate が複数リクエストを並行処理しうる |
| 配置 | リージョンを選んでデプロイ | 世界中のエッジに自動配置 |
| 主言語 | Python, Node.js, Java, Go ほか多数 | **JavaScript / TypeScript**(Python は Python Workers として提供、Pyodide/WASM ベース) |
| ライブラリ | pip / npm などほぼ自由、ネイティブ拡張も可 | Web 標準 API 中心。Node 互換は部分的、ネイティブ拡張は不可 |
| 実行時間 | 最大 15 分 | CPU 時間に上限あり(長時間処理は Queues / Workflows / Durable Objects へ) |
| 課金 | 呼び出し回数 × 実行時間 × メモリ | リクエスト数 + CPU 時間(待ち時間は課金されにくい) |
| 状態 | 持たない前提 | 同じく持たない前提(状態は KV / D1 / Durable Objects) |

→ 「重い依存や長時間処理を Python でやる」なら Lambda、
「軽い API・エッジでの低遅延・JS/TS 中心」なら Workers が向きます。

## 3. ハンドラの書き方の対比

Lambda(このガイドの Step 3 相当):

```python
def handler(event, context):
    return {"statusCode": 200, "body": "ok"}
```

Workers(TypeScript。`Request` を受けて `Response` を返す Web 標準の形):

```ts
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return new Response("ok", { status: 200 });
  },
};
```

| Lambda | Workers |
|--------|---------|
| `event`(トリガーごとに形が違う JSON) | `Request`(標準の Fetch API)。他トリガーは `scheduled` / `queue` など別ハンドラ |
| `context` | `ctx`(`waitUntil` でレスポンス後に処理を続けられる) |
| 環境変数 / Secrets Manager | `env`(vars / secrets / **バインディング**) |
| 戻り値は dict(`statusCode`, `body`) | `Response` オブジェクト |
| ルーティングは API Gateway か関数内 | 関数内(Hono などの軽量ルータが定番) |

### バインディングという考え方

Lambda では「実行ロール(IAM)」で DynamoDB や S3 へ権限を与え、SDK で接続します。
Workers では設定ファイルで **バインディング** を宣言すると、`env.DB` や `env.BUCKET` として
そのまま使えます(認証情報や接続文字列をコードに書かない)。

```jsonc
// wrangler.jsonc(抜粋)
{
  "name": "todo-api",
  "main": "src/index.ts",
  "d1_databases": [{ "binding": "DB", "database_name": "todo", "database_id": "<ID>" }]
}
```

## 4. データ層: DynamoDB と D1

このガイドの Todo API は DynamoDB を使っています。同じものを D1 で作ると考え方が変わります。

| 観点 | DynamoDB | D1 |
|------|----------|-----|
| モデル | キーバリュー / ドキュメント(アクセスパターンから設計) | **リレーショナル(SQL / SQLite)** |
| 設計の起点 | パーティションキー / ソートキー / GSI | テーブル / インデックス / JOIN |
| マイグレーション | スキーマレス(属性は自由) | `wrangler d1 migrations`(SQL ファイル) |
| スケール | 水平に非常に強い | 1 DB あたりのサイズに上限あり。小〜中規模向け(DB を分ける設計も) |
| 接続 | SDK(IAM 認証) | バインディング経由(接続管理なし) |

```ts
// D1 での Todo 取得(Step 5 の get に相当)
const { results } = await env.DB
  .prepare("SELECT id, title, done FROM todos WHERE id = ?")
  .bind(id)
  .all();
```

SQL を書き慣れていれば D1 のほうが入りやすく、高スループットな単純キー参照や
巨大データなら DynamoDB が有利、という住み分けです。

## 5. Pages と Lambda の関係

Pages は「Lambda の代替」ではなく **フロントエンド(静的ファイル)のホスティング** です。

- 静的な HTML/JS/CSS を Git 連携で自動ビルド・配信(AWS なら S3 + CloudFront / Amplify に近い)
- サーバー側処理が必要なら Pages Functions(中身は Workers)を併用
- 現在は Workers 側に静的アセット配信が統合されつつあり、新規は Workers 中心の構成も選べます

典型構成の対比:

```
AWS:        ブラウザ → CloudFront(S3: 静的) → API Gateway → Lambda → DynamoDB
Cloudflare: ブラウザ → Pages(静的)         → Workers          → D1
```

## 6. どちらを選ぶか

| 状況 | 向く選択 |
|------|---------|
| 既に AWS を使っている / IAM・VPC・他の AWS サービスと密結合 | Lambda |
| Python のライブラリ資産・ネイティブ拡張を使いたい | Lambda |
| 数分以上の処理、大きなペイロード | Lambda |
| 世界中のユーザーに低遅延で返したい軽量 API | Workers |
| JS/TS 中心で、サーバー管理と設定を最小にしたい | Workers + D1 / Pages |
| 小規模サービスを無料枠で始めたい | どちらも無料枠あり(条件は公式で確認) |

両者は排他的ではなく、フロントと軽い API は Cloudflare、重い処理や既存基盤は AWS、
という併用もよくあります。

## 7. このガイドの用語の読み替え

| このガイド | Cloudflare での読み替え |
|-----------|-----------------------|
| ハンドラ `handler(event, context)` | `fetch(request, env, ctx)` |
| 実行ロール(IAM) | バインディング + API トークンの権限 |
| コールド スタート対策(Init で再利用) | isolate 単位の再利用はあるが、気にする場面は少ない |
| SAM / CDK | Wrangler(`wrangler deploy`) |
| CloudWatch Logs | Workers Logs / `wrangler tail` |
| DLQ / 部分バッチ失敗 | Queues の retry / dead letter queue |

## 🔗 参考

- [Cloudflare Workers](https://developers.cloudflare.com/workers/)
- [Cloudflare D1](https://developers.cloudflare.com/d1/)
- [Cloudflare Pages](https://developers.cloudflare.com/pages/)
- [Workers の制限](https://developers.cloudflare.com/workers/platform/limits/) / [料金](https://developers.cloudflare.com/workers/platform/pricing/)
- [Python Workers](https://developers.cloudflare.com/workers/languages/python/)
