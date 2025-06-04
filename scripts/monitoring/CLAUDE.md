# monitoring 디렉토리 가이드

봇 상태 모니터링 및 데이터 확인 스크립트들이 위치한 디렉토리입니다.

## 주요 스크립트

### check_bot_status.py
- **목적**: 실행 중인 봇 상태 확인
- **사용 시기**: 일일 점검, 문제 발생 시
- **확인 항목**:
  - 봇 프로세스 실행 여부
  - 메모리 사용량
  - 최근 활동 시간
  - 에러 로그 분석

### check_gist_data.py
- **목적**: GitHub Gist 데이터 무결성 확인
- **사용 시기**: 데이터 동기화 문제 의심 시
- **확인 항목**:
  - Gist 접근 가능 여부
  - 데이터 형식 검증
  - 마지막 업데이트 시간
  - 로컬 데이터와 비교

## 사용 예시
```bash
# 봇 상태 확인
python scripts/monitoring/check_bot_status.py

# Gist 데이터 검증
python scripts/monitoring/check_gist_data.py --verbose
```

## 모니터링 권장 사항
- 일일 1회 이상 상태 확인
- 크론탭으로 자동화 가능
- 이상 감지 시 알림 설정
- 로그 파일 주기적 확인