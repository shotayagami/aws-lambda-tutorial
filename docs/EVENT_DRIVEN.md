# Step 8-9: イベント駆動 (S3 / SQS)

コード: [step8_s3_trigger.py](../src/step8_s3_trigger.py) / [step9_sqs_worker.py](../src/step9_sqs_worker.py)
テンプレート: [template-events.yaml](../template-events.yaml)

## 呼び出し方式の違い

| | S3 | SQS |
|---|---|---|
| 呼び出し | S3 が Lambda を **非同期** に呼ぶ | Lambda が SQS を **ポーリング** |
| 1 回の event | Records 配列(通常 1 件) | 最大 `BatchSize` 件 |
| 失敗時 | 自動リトライ(既定 2 回)後、送信先/DLQ | メッセージが可視化され再配信 -> `maxReceiveCount` 超過で DLQ |
| 重複 | あり得る | あり得る(少なくとも 1 回配信) |

どちらも **冪等**(同じ入力を 2 回処理しても結果が同じ)に作るのが大前提です。

## S3 トリガー (Step 8)

- キーは **URL エンコードされて届く**(スペースは `+`)。`urllib.parse.unquote_plus` で戻す
- **同じバケットに書き戻すと無限ループ**。出力は別バケット、または `Filter`(prefix/suffix)で入力側だけに絞る
- 大きなファイルは `read()` で全部メモリに載せず、ストリーム処理か `/tmp` を使う
- 実行ロールは対象バケットの読み取りだけ(`S3ReadPolicy`)

## SQS トリガー (Step 9)

### 部分バッチ レスポンス(最重要)

何もしないと、**1 件でも例外を投げるとバッチ全体が再配信**されます(成功済みも含む)。

```yaml
FunctionResponseTypes:
  - ReportBatchItemFailures
```

```python
return {"batchItemFailures": [{"itemIdentifier": record["messageId"]}]}  # 失敗した分だけ
```

### キュー設定の目安

| 設定 | 目安 | 理由 |
|------|------|------|
| `VisibilityTimeout` | 関数 Timeout の 6 倍以上 | 処理中のメッセージが二重に処理されるのを防ぐ |
| `maxReceiveCount` | 3〜5 | 何度も失敗する「毒メッセージ」を DLQ へ退避 |
| DLQ の保持期間 | 14 日 | 原因調査の時間を確保 |
| `BatchSize` | 用途次第(1〜10 から) | 大きいほど効率的だが、失敗時の影響範囲も増える |

### 同時実行数の制御

SQS は負荷に応じて Lambda を増やします。下流(DB など)を守りたい場合は、
イベント ソース マッピングの `ScalingConfig.MaximumConcurrency` で上限を設定します。

## 運用の注意

- **DLQ を監視する**(メッセージ数のアラーム)。溜まっていても気づけないのが最も多い事故
- ログに `message_id` / `key` を出して追跡できるようにする
- 外部 API を呼ぶ処理は、タイムアウトとリトライの上限を関数側でも持つ

## 実行

```bash
python src/step8_s3_trigger.py
python src/step9_sqs_worker.py     # msg-1, msg-2 だけが失敗として返る
```
