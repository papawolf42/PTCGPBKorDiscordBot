# testing 디렉토리 가이드

자동화 테스트 관련 스크립트와 테스트 케이스들이 위치한 디렉토리입니다.

## 디렉토리 구조

### test_simulator.py
- **목적**: Poke.py 자동화 테스트 메인 실행기
- **기능**:
  - 봇과 테스트 클라이언트 동시 실행
  - 테스트 케이스 순차 실행
  - 결과 수집 및 리포트 생성

### test_cases/
- **목적**: 개별 테스트 케이스 모듈
- **구성**:
  - `test_connection.py`: 봇 연결 및 초기화 테스트
  - `test_messages.py`: HEARTBEAT 메시지 처리 테스트
  - `test_commands.py`: 명령어 응답 테스트
  - `test_background.py`: 백그라운드 작업 테스트

### results/
- **목적**: 테스트 결과 파일 저장
- **파일 형식**: `test_results_YYYYMMDD_HHMMSS.json`
- **내용**: 테스트 성공/실패, 로그, 타이밍 정보

## 테스트 실행 방법

```bash
# 전체 테스트 실행
python scripts/testing/test_simulator.py

# 특정 테스트만 실행
python scripts/testing/test_simulator.py --only connection

# 실패 시 중단
python scripts/testing/test_simulator.py --stop-on-failure
```

## 테스트 작성 가이드

1. **독립성**: 각 테스트는 다른 테스트에 의존하지 않음
2. **원자성**: 하나의 기능만 테스트
3. **반복가능**: 여러 번 실행해도 같은 결과
4. **명확한 검증**: 성공/실패 기준 명시

## 주의사항
- 테스트는 TEST_MODE=true 환경에서만 실행
- data_test/ 디렉토리 사용
- 실제 Discord 채널에 메시지 전송됨
- 테스트 후 정리(cleanup) 필수