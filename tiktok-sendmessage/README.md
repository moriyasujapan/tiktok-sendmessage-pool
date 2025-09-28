# TikTok SendMessage Pool - Enhanced Bot Detection Bypass

TikTokのBot検出を回避するための高度なメッセージ送信システム

## セットアップ

1. 環境変数の設定
```bash
cp .env.example .env
# .envファイルを編集して認証情報を設定
```

2. Docker環境での実行
```bash
docker-compose up -d
```

3. 直接実行
```bash
pip install -r requirements.txt
python api_server.py
```

## API エンドポイント

- POST /connect - セッション作成
- POST /send - メッセージ送信  
- POST /disconnect - セッション終了
- GET /health - ヘルスチェック
- GET /status - ステータス確認

## 機能

- 高度なBot検出回避
- リアルタイム監視システム
- 自動プロキシローテーション
- 適応的遅延システム
- セッション管理とキャッシュ

詳細な実装ガイドは implementation_guide.md を参照してください。
