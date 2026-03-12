# 語音控制小車工具

通過WebSocket連接ROS2系統，發送語音指令控制小車移動的TEN Framework擴充功能。

## 功能

- 通過WebSocket連接到ROS2小車控制系統
- 發送語音指令控制小車移動（前進、後退、左轉、右轉、停止等）
- 支援超時和錯誤處理

## 工具

### control_car

控制小車移動的語音指令工具。

**參數：**
- `command` (string, 必需): 語音指令，例如「向前移動3秒」、「向後移動2秒」、「左轉」、「右轉」、「停止」

## 設定

請參考 [property.json] 中的設定項：

- `ws_url`: WebSocket伺服器URL，預設 `ws://60.205.136.51:8765/robot_control`
- `timeout`: 超時時間（秒），預設30秒

可通過環境變數 `CAR_CONTROL_WS_URL` 覆蓋WebSocket URL。

## 開發

### 建置

```bash
pip install -r requirements.txt
```

### 單元測試

```bash
pytest tests/
```
