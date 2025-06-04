# src 디렉토리 가이드

소스 코드 루트 디렉토리입니다.

## 디렉토리 구조

### bots/
- **역할**: Discord 봇 실행 파일들
- **파일들**:
  - `Poke.py`: Gist 기반 (Group7, Group8)
  - `Poke2.py`: 메인 갓팩 봇
  - `Poke20.py`: 20% 팩 전용
  - `Poke3.py`: 포럼 관리
  - `Poke4.py`: 테스트용
- **주의**: 각 봇은 독립 실행 (병렬 구조)

### modules/
- **역할**: 공통 모듈
- **파일들**:
  - `GIST.py`: GitHub Gist API 연동
  - `GroupInfo.py`: 그룹 정보 관리
  - `LocalFile.py`: 로컬 파일 시스템
  - `LocalFileAdapter.py`: Gist → LocalFile 어댑터
- **주의**: 봇들이 공통으로 import하여 사용

### utils/
- **역할**: 유틸리티 함수
- **파일들**:
  - `deleteOldPost.py`: 오래된 포스트 삭제
- **주의**: 독립적인 헬퍼 스크립트

## ⚠️ 현재 상태
- import 경로 수정 필요 (파일 이동으로 인한 경로 불일치)
- 예: `from GIST import *` → `from src.modules.GIST import *`