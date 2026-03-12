# 音声制御カーコントロールツール

ROS2システムへのWebSocket接続経由で音声コマンドを送信して車を制御するTEN Framework拡張機能。

## 機能

- WebSocket経由でROS2カーコントロールシステムに接続
- 音声コマンドで車の移動を制御（前進、後退、左折、右折、停止など）
- タイムアウトとエラー処理をサポート

## ツール

### control_car

音声コマンドで車を制御するツール。

**パラメータ：**
- `command` (string, 必須): 音声コマンド、例：「3秒前進」、「2秒後退」、「左折」、「右折」、「停止」

## 設定

[property.json]の設定を参照：

- `ws_url`: WebSocketサーバURL、デフォルト `ws://60.205.136.51:8765/robot_control`
- `timeout`: タイムアウト（秒）、デフォルト30

環境変数 `CAR_CONTROL_WS_URL` でWebSocket URLをオーバーライドできます。

## 開発

### ビルド

```bash
pip install -r requirements.txt
```

### ユニットテスト

```bash
pytest tests/
```
