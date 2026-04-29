# 음성 제어 휴머노이드 로봇 도구

HTTP API를 통해 휴머노이드 로봇을 제어하는 TEN Framework 확장 프로그램 (액션 제어 및 TTS).

## 기능

- 액션 제어: 로봇이 사전 정의된 액션 수행 (악수, 손흔들기, 보행 등)
- TTS 음성: 로봇이 말하게 하기
- 시간 초과 및 오류 처리 지원

## 도구

### control_robot_action

로봇이 사전 정의된 액션을 수행하도록 합니다.

**매개변수:**
- `action_name` (string, 필수): 액션 이름, 예: "双手居中", "握手", "挥手", "走路"

### robot_speak

로봇이 말하게 합니다 (TTS).

**매개변수:**
- `text` (string, 필수): 말할 텍스트

## 설정

[property.json]의 설정을 참조하세요:

- `server_url`: 로봇 서버 URL, 기본값 `http://60.205.136.51:6003`
- `timeout`: 시간 초과 (초), 기본값 30

환경 변수 `ROBOT_SERVER_URL`로 서버 URL을 재정의할 수 있습니다.

## 개발

### 빌드

```bash
pip install -r requirements.txt
```

### 단위 테스트

```bash
pytest tests/
```
