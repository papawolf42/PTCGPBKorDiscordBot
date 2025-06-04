# scripts 디렉토리 가이드

독립 실행 가능한 유틸리티 스크립트들이 위치한 디렉토리입니다.

## 디렉토리 구조

```
scripts/
├── migration/           # 데이터 마이그레이션 관련
│   ├── migrate_to_local.py
│   ├── copy_to_test.py
│   └── CLAUDE.md
│
├── monitoring/          # 상태 모니터링 관련
│   ├── check_bot_status.py
│   ├── check_gist_data.py
│   └── CLAUDE.md
│
└── testing/            # 테스트 자동화 관련
    ├── test_simulator.py
    ├── test_cases/     # 개별 테스트 케이스
    │   ├── __init__.py
    │   └── CLAUDE.md
    ├── results/        # 테스트 결과 저장
    │   └── .gitkeep
    └── CLAUDE.md
```

## 사용 가이드

### 마이그레이션
```bash
# Gist → 로컬 파일 전환
python scripts/migration/migrate_to_local.py

# 테스트 환경 데이터 복사
python scripts/migration/copy_to_test.py
```

### 모니터링
```bash
# 봇 상태 확인
python scripts/monitoring/check_bot_status.py

# Gist 데이터 검증
python scripts/monitoring/check_gist_data.py
```

### 테스트
```bash
# 자동화 테스트 실행
python scripts/testing/test_simulator.py
```

## 사용 시나리오
1. **일일 점검**: `check_bot_status.py` 실행
2. **문제 발생 시**: `check_gist_data.py`로 데이터 확인
3. **마이그레이션**: `migrate_to_local.py` 단계별 실행

## 주의사항
- 스크립트 실행 전 봇 중지 권장
- 백업 후 실행
- 로그 파일 확인