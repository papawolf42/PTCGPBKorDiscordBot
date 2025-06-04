# 상대경로 문제 해결 방안

## 문제점
- Poke.py 등이 `data/` 디렉토리를 상대경로로 사용
- `src/bots/`로 이동하면 `src/bots/data/`에 저장하게 됨

## 해결 방안

### 방안 1: 프로젝트 루트 경로 설정 (추천)
```python
# src/modules/base_path.py
import os
import sys

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# Python 경로에 추가
sys.path.insert(0, PROJECT_ROOT)
```

각 봇 파일 상단에 추가:
```python
# src/bots/Poke2.py
from src.modules.base_path import PROJECT_ROOT, DATA_DIR
import os

# 기존 코드
# with open('data/heartbeat_data/...', 'w') as f:

# 수정 후
# with open(os.path.join(DATA_DIR, 'heartbeat_data/...'), 'w') as f:
```

### 방안 2: 심볼릭 링크 사용
```bash
# src/bots/ 디렉토리에 data 심볼릭 링크 생성
cd src/bots/
ln -s ../../data data

# tests/ 디렉토리에도 동일하게
cd ../../tests/
ln -s ../data data
```

### 방안 3: 실행 스크립트 사용
```bash
# run_bot.sh
#!/bin/bash
cd /path/to/PTCGPBkor  # 항상 루트에서 실행
python src/bots/Poke2.py
```

### 방안 4: 환경변수 활용
```python
# .env에 추가
DATA_PATH=/Users/papawolf/Dev/PTCGPBkor/data

# 봇 코드에서
import os
from dotenv import load_dotenv
load_dotenv()

DATA_PATH = os.getenv('DATA_PATH', 'data')  # 기본값은 상대경로
```

## 권장 조합
1. **개발 시**: 심볼릭 링크 (방안 2) - 코드 수정 불필요
2. **장기적**: 프로젝트 루트 설정 (방안 1) - 더 깔끔하고 portable
3. **당장**: 현재 구조 유지하고 문서화만 개선