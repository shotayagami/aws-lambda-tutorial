# Step 10: Cognito + JWT 認証

コード: [step10_jwt_claims.py](../src/step10_jwt_claims.py)
テンプレート: [template-auth.yaml](../template-auth.yaml)

## 全体像

```
[クライアント] --(1) サインイン--> [Cognito User Pool] --> JWT (ID / アクセス トークン)
      |
      +--(2) Authorization: Bearer <JWT> --> [API Gateway HTTP API: JWT オーソライザー]
                                                 | 署名・有効期限・issuer・audience を検証
                                                 v (通った時だけ)
                                             [Lambda: claims を読んで認可]
```

- **トークンの検証は API Gateway が行う**。Lambda にライブラリは不要
- 検証に通った JWT のクレームは `event["requestContext"]["authorizer"]["jwt"]["claims"]`、
  スコープは `["jwt"]["scopes"]` に入る

## 認証と認可の分担

| | 担当 | 例 |
|---|------|----|
| 認証(誰か) | API Gateway + Cognito | トークンが正当か |
| 認可(何を許すか) | **Lambda(あなたのコード)** | scope の確認、他人のデータに触れさせない |

最も多い事故は **IDOR**(他人の ID を URL に入れると他人のデータが見える)です。
データのキーには必ずトークン由来の `sub` を使い、URL やボディの `user_id` を信用しないでください。

## ID トークンとアクセス トークン

| | 用途 | audience の検証 |
|---|------|------|
| ID トークン | 「誰か」をクライアントが知る | `aud` = アプリ クライアント ID |
| アクセス トークン | API を呼ぶ | `client_id` = アプリ クライアント ID、`scope` を持つ |

API 呼び出しには **アクセス トークン** を使うのが基本です(スコープで認可できるため)。
スコープを使うには、Cognito にリソース サーバーとカスタム スコープ(例: `notes/read`)の設定が必要です。

## 動かし方(概要)

```bash
sam deploy --template-file template-auth.yaml --guided   # ※ 先に sam build
```

トークン取得はクライアント(Amplify / AWS SDK / Hosted UI)に任せるのが一般的です。
動作確認のみなら、AWS CLI でテスト ユーザーを作成してサインインします
(ALLOW_USER_PASSWORD_AUTH などのフローをテスト用に一時有効化する必要があります)。

```bash
curl -H "Authorization: Bearer $TOKEN" https://xxxx.execute-api.<region>.amazonaws.com/notes
```

## チェックリスト

- [ ] 関数は API Gateway 経由でのみ呼べる(Function URL を併用しない)
- [ ] `sub` でデータを絞っている(他人のデータに触れない)
- [ ] 必要な scope を関数側でも確認している
- [ ] CORS の `AllowOrigins` を `*` にしていない
- [ ] トークンやクレームの内容をログに出していない

## Entra ID など他の IdP

JWT オーソライザーは **OIDC 準拠なら Cognito 以外でも使えます**。
`issuer` と `audience` を IdP の値に変えるだけです(Entra ID, Auth0, Okta など)。
