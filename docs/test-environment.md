# Discord 봇 테스트 환경 설정

## 현재 상황
- 라이브 서비스 중인 봇을 직접 수정 → 버그 발생 시 사용자 영향
- 여러 봇이 병렬 실행 중 (Poke.py, Poke2.py, Poke20.py)
- 동일한 봇 토큰 사용 가능 (Discord는 중복 접속 허용)

## 테스트 환경 구축 방안

### 1. TEST_MODE 플래그
```python
# config.py 또는 각 봇 파일 상단
import os

TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# 실행 방법
# TEST_MODE=true python Poke.py
```

### 2. 채널 격리
```python
# 테스트 전용 채널 ID
if TEST_MODE:
    ALLOWED_CHANNELS = {
        'HEARTBEAT': 테스트_하트비트_채널_ID,
        'DETECT': 테스트_감지_채널_ID,
        'COMMAND': 테스트_명령어_채널_ID,
        'POSTING': 테스트_포럼_ID
    }
else:
    ALLOWED_CHANNELS = {
        'HEARTBEAT': 실제_하트비트_채널_ID,
        'DETECT': 실제_감지_채널_ID,
        'COMMAND': 실제_명령어_채널_ID,
        'POSTING': 실제_포럼_ID
    }

# 메시지 처리 시
@bot.event
async def on_message(message):
    if message.channel.id not in ALLOWED_CHANNELS.values():
        return  # 지정된 채널이 아니면 무시
```

### 3. 데이터 경로 분리
```python
# 테스트 모드일 때 다른 폴더 사용
if TEST_MODE:
    DATA_PATH = "data_test/"
    GIST_PREFIX = "TEST_"  # Gist 파일명에 TEST_ 접두사
else:
    DATA_PATH = "data/"
    GIST_PREFIX = ""
```

### 4. 명령어 구분 (선택사항)
```python
# 테스트 모드에서는 다른 prefix 사용
COMMAND_PREFIX = "?" if TEST_MODE else "!"

# 사용 예: ?barrack (테스트), !barrack (실제)
```

### 5. 로그 강화
```python
import logging

if TEST_MODE:
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('TestBot')
else:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('LiveBot')
```

## 구현 우선순위

### Phase 1: Poke.py Gist → 로컬 파일 전환
**목적**: GitHub Gist 의존성 제거, 로컬 파일 시스템으로 전환

**현재 Gist 사용 항목**:
1. 온라인 사용자 목록
2. 갓팩 정보
3. 서버 설정

**전환 계획**:
```
Gist 구조                    →  로컬 파일 구조
├── online_users.txt         →  data/online_users.json
├── god_packs.json          →  data/god_packs.json
└── server_config.json      →  data/server_config.json
```

**마이그레이션 전략**:
1. 읽기 함수부터 이중화 (Gist 실패 시 로컬 파일 읽기)
2. 쓰기 함수 이중화 (로컬 + Gist 동시 저장)
3. 안정화 후 Gist 의존성 완전 제거

### Phase 2: 테스트 환경 구축
1. TEST_MODE 플래그 구현
2. 테스트 채널 생성 및 ID 설정
3. 테스트 데이터 폴더 구조 생성

### Phase 3: 통합 테스트
1. 테스트 모드로 봇 실행
2. 주요 기능 검증
3. 데이터 무결성 확인

## 장점
- 라이브 서비스 영향 없이 개발/테스트 가능
- 같은 Discord 서버에서 테스트 가능
- 데이터 충돌 방지
- 빠른 롤백 가능 (테스트 코드 삭제만 하면 됨)

## 주의사항
- 테스트 채널은 일반 사용자가 접근하지 못하도록 권한 설정
- 테스트 데이터는 주기적으로 정리
- 실제 서비스 전환 시 충분한 검증 필요