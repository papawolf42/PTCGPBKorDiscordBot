# modules 디렉토리 가이드

봇들이 공통으로 사용하는 모듈들이 위치한 디렉토리입니다.

## 모듈별 상세 정보

### paths.py ⭐ NEW
- **기능**: 프로젝트 경로 관리
- **주요 기능**:
  - 프로젝트 루트 자동 탐색 (CLAUDE.md 기준)
  - 주요 디렉토리 경로 제공 (`PROJECT_ROOT`, `DATA_DIR`, `LOGS_DIR`)
  - 디렉토리 생성 함수 (`ensure_directories()`)
- **사용법**:
  ```python
  from ..modules.paths import DATA_DIR, ensure_directories
  HEARTBEAT_DIR = os.path.join(DATA_DIR, "heartbeat_data")
  ensure_directories("heartbeat_data", "user_data", "raw")
  ```
- **사용처**: 모든 봇 (경로 일관성 보장)

### GIST.py
- **기능**: GitHub Gist API와의 통신
- **주요 클래스/함수**:
  - Gist 읽기/쓰기
  - 온라인 사용자 목록 관리
  - 갓팩 정보 저장/조회
- **사용처**: `Poke.py`

### GroupInfo.py
- **기능**: Discord 그룹 정보 관리
- **주요 내용**:
  - 각 그룹의 채널 ID 정의
  - 그룹별 태그 ID 관리
  - 환경 변수 로드
- **사용처**: 모든 봇

### LocalFile.py
- **기능**: 로컬 파일 시스템 접근
- **주요 기능**:
  - JSON 파일 읽기/쓰기
  - 디렉토리 관리
  - 백업 생성
- **사용처**: `Poke2.py`, `Poke20.py`

### GISTAdapter.py ⭐ NEW
- **기능**: GIST 인터페이스로 LocalFile 사용
- **주요 기능**:
  - GIST와 100% 동일한 인터페이스 제공
  - 내부적으로 LocalFile 사용
  - SERVER, USER 클래스 포함
  - import 한 줄만 변경하여 전환 가능
- **사용처**: `Poke.py` (GIST → LocalFile 전환됨)

## 의존성 관계
```
paths.py ← 모든 봇 (경로 관리)
GIST.py ← Poke.py
GroupInfo.py ← 모든 봇 (그룹 설정)
LocalFile.py ← Poke2.py, Poke20.py
LocalFileAdapter.py ← 마이그레이션 테스트
```

## 주의사항
- 모듈 수정 시 모든 봇에 영향 가능
- 백업 후 수정 권장
- 환경 변수 필수 확인