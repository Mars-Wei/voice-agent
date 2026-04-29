# 語音控制人形機器人工具

通過HTTP API控制人形機器人（動作和TTS語音）的TEN Framework擴充功能。

## 功能

- 動作控制：控制機器人執行預定義動作（握手、揮手、走路等）
- TTS語音：讓機器人說話，通過TTS系統播放
- 支援超時和錯誤處理

## 工具

### control_robot_action

控制機器人執行預定義動作。

**參數：**
- `action_name` (string, 必需): 動作名稱，如「雙手居中」、「握手」、「揮手」、「走路」

**支援的動作：**
- 手臂動作：雙手居中、握手、揮手、手臂伸展、手臂擺動
- 身體動作：下蹲、起立、左傾斜、右傾斜
- 行走動作：走路、停止走路、左轉、右轉

### robot_speak

讓機器人說話（TTS語音合成）。

**參數：**
- `text` (string, 必需): 要播放的文字

## 設定

請參考 [property.json] 中的設定項：

- `server_url`: 機器人伺服器URL，預設 `http://60.205.136.51:6003`
- `timeout`: 超時時間（秒），預設30秒

可通過環境變數 `ROBOT_SERVER_URL` 覆蓋伺服器URL。

## 開發

### 建置

```bash
pip install -r requirements.txt
```

### 單元測試

```bash
pytest tests/
```
