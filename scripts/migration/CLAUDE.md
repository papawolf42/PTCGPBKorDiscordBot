# migration 디렉토리 가이드

데이터 마이그레이션 및 전환 관련 스크립트들이 위치한 디렉토리입니다.

## 주요 스크립트

### migrate_to_local.py
- **목적**: GitHub Gist → 로컬 파일 시스템 전환
- **사용 시기**: Poke.py를 LocalFile 방식으로 전환할 때
- **주요 기능**:
  - Gist 데이터 백업
  - 로컬 파일로 변환 및 저장
  - 데이터 검증
  - 마이그레이션 로그 생성

### copy_to_test.py
- **목적**: 실제 데이터를 테스트 환경으로 복사
- **사용 시기**: 테스트 환경 구축 시
- **주요 기능**:
  - data/ → data_test/ 복사
  - admin.txt 테스트용 ID로 변경
  - 테스트 데이터 초기화

## 사용 예시
```bash
# Gist에서 로컬로 마이그레이션
python scripts/migration/migrate_to_local.py

# 테스트 환경 구축
python scripts/migration/copy_to_test.py
```

## 주의사항
- 마이그레이션 전 백업 필수
- 봇 실행 중 마이그레이션 금지
- 테스트 데이터는 실제 사용자 정보 포함 주의