# scripts 디렉토리 가이드

독립 실행 가능한 유틸리티 스크립트들이 위치한 디렉토리입니다.

## 스크립트별 상세 정보

### check_bot_status.py
- **기능**: 봇 상태 및 데이터 파일 확인
- **확인 항목**:
  - 봇 프로세스 실행 여부
  - 데이터 파일 무결성
  - 최근 활동 시간
  - 에러 로그 분석
- **실행**: `python scripts/check_bot_status.py`

### check_gist_data.py
- **기능**: GitHub Gist 데이터 확인 및 검증
- **확인 항목**:
  - Gist 접근 가능 여부
  - 데이터 형식 검증
  - 마지막 업데이트 시간
  - 로컬 데이터와 동기화 상태
- **실행**: `python scripts/check_gist_data.py`

### migrate_to_local.py
- **기능**: Gist → LocalFile 마이그레이션
- **주요 작업**:
  - Gist 데이터 백업
  - 로컬 파일로 변환
  - 데이터 검증
  - 롤백 옵션 제공
- **실행**: `python scripts/migrate_to_local.py --backup`

## 사용 시나리오
1. **일일 점검**: `check_bot_status.py` 실행
2. **문제 발생 시**: `check_gist_data.py`로 데이터 확인
3. **마이그레이션**: `migrate_to_local.py` 단계별 실행

## 주의사항
- 스크립트 실행 전 봇 중지 권장
- 백업 후 실행
- 로그 파일 확인