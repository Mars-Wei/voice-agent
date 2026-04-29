# 音声制御ヒューマノイドロボットツール

HTTP API経由でヒューマノイドロボットを制御するTEN Framework拡張機能（アクション制御とTTS）。

## 機能

- アクション制御：ロボットに事前定義アクションを実行させる（握手、挥手、歩行など）
- TTS音声：ロボットに話させる
- タイムアウトとエラー処理をサポート

## ツール

### control_robot_action

ロボットに事前定義アクションを実行させる。

**パラメータ：**
- `action_name` (string, 必須): アクション名、例：「双手居中」、「握手」、「挥手」、「走路」

### robot_speak

ロボットに話させる（TTS）。

**パラメータ：**
- `text` (string, 必須): 話すテキスト

## 設定

[property.json]の設定を参照：

- `server_url`: ロボットサーバURL、デフォルト `http://60.205.136.51:6003`
- `timeout`: タイムアウト（秒）、デフォルト30

環境変数 `ROBOT_SERVER_URL` でサーバURLをオーバーライドできます。

## 開発

### ビルド

```bash
pip install -r requirements.txt
```

### ユニットテスト

```bash
pytest tests/
```
