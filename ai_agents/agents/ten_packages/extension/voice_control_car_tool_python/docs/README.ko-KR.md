# 음성 제어 자동차 도구

ROS2 시스템에 WebSocket 연결을 통해 음성 명령을 전송하여 자동차를 제어하는 TEN Framework 확장 프로그램입니다.

## 기능

- WebSocket을 통해 ROS2 자동차 제어 시스템에 연결
- 음성 명령으로 자동차 이동 제어 (전진, 후진, 좌회전, 우회전, 정지 등)
- 시간 초과 및 오류 처리 지원

## 도구

### control_car

음성 명령으로 자동차를 제어하는 도구.

**매개변수:**
- `command` (string, 필수): 음성 명령, 예: "3초 전진", "2초 후진", "좌회전", "우회전", "정지"

## 설정

[property.json]의 설정을 참조하세요:

- `ws_url`: WebSocket 서버 URL, 기본값 `ws://60.205.136.51:8765/robot_control`
- `timeout`: 시간 초과 (초), 기본값 30

환경 변수 `CAR_CONTROL_WS_URL`로 WebSocket URL을 재정의할 수 있습니다.

## 개발

### 빌드

```bash
pip install -r requirements.txt
```

### 단위 테스트

```bash
pytest tests/
```
