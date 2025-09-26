# TikTok SendMessage Microservice (Connection Pool)

# 開発中(This product is currently under development)

**tiktok-live-connector** を使って **sendMessage 専用 API** を提供します。  
起動時に **Selenium で TikTok にログイン → `sessionid` と `tt-target-idc` を自動取得**し、
**常時コネクション再利用（プール）** で高速に送信します。

> 注意: これは非公式ライブラリです。TikTok の仕様変更で動作が変わる場合があります。

## 機能
- `POST /connect` … 指定の `uniqueId` へ接続（常駐）
- `POST /send` … 常駐コネクションを使って即時送信
- `POST /disconnect` … 該当 `uniqueId` のコネクションを解放
- `GET /health` … ヘルスチェック

## 使い方（Docker）
```bash
cp .env.example .env   # 必要に応じて編集（初回は manual ログイン推奨）
docker compose up
# → セレニウムのブラウザで TikTok ログインを完了すると cookies.json が作成されます
```

### 送信
# 1) 事前に接続（常駐）

```bash
curl -X POST http://localhost:3000/connect -H 'Content-Type: application/json' -d '{"uniqueId":"配信者"}'
```

# 2) 送信（即時）
```bash
curl -X POST http://localhost:3000/send -H 'Content-Type: application/json' -d '{"uniqueId":"配信者","message":"こんにちは"}'
```

### 切断
```bash
curl -X POST http://localhost:3000/disconnect -H 'Content-Type: application/json' -d '{"uniqueId":"配信者"}'
```

### 環境変数とファイルは .env.example を参照してください。
（初期状態として“REPLACE”のプレースホルダーを入れています。Selenium 起動後、実際の値に置き換えられます。）
```yaml
## `cookies.json`

```json
{
  "sessionid": "REPLACE",
  "tt-target-idc": "REPLACE"
}
```

