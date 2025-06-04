# .env를 활용한 절대경로 해결책

## 1. .env 파일에 추가
```bash
# .env
PROJECT_ROOT=/Users/papawolf/Dev/PTCGPBkor
DATA_PATH=/Users/papawolf/Dev/PTCGPBkor/data
```

## 2. 봇 코드 수정 (최소한의 변경)
```python
# Poke2.py 예시
import os
from dotenv import load_dotenv

load_dotenv()
DATA_PATH = os.getenv('DATA_PATH', 'data')  # 기본값은 현재 상대경로

# 기존 코드
# file_path = f"data/heartbeat_data/{user_id}.json"

# 수정 후
file_path = os.path.join(DATA_PATH, f"heartbeat_data/{user_id}.json")
```

## 3. 장점
- ✅ 파일 위치가 바뀌어도 .env만 수정하면 됨
- ✅ 개발/테스트/운영 환경별로 다른 경로 설정 가능
- ✅ 기존 코드와 호환 (DATA_PATH 없으면 'data' 사용)
- ✅ 심볼릭 링크 관리 불필요
- ✅ 명시적이고 이해하기 쉬움

## 4. 환경별 설정
```bash
# .env (운영)
DATA_PATH=/Users/papawolf/Dev/PTCGPBkor/data

# .env.test (테스트)
DATA_PATH=/Users/papawolf/Dev/PTCGPBkor/data_test

# .env.dev (개발)
DATA_PATH=/Users/papawolf/Dev/PTCGPBkor/data_dev
```

## 5. 마이그레이션 단계
1. 먼저 .env에 DATA_PATH 추가
2. 한 파일씩 점진적으로 수정
3. 테스트 후 파일 구조 변경

이 방법이 가장 실용적이고 깔끔합니다!