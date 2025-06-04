# test_cases 디렉토리 가이드

개별 테스트 케이스 모듈들이 위치한 디렉토리입니다.

## 테스트 케이스 구조

각 테스트 파일은 다음 구조를 따릅니다:

```python
class TestCaseName:
    def __init__(self, client, channels):
        self.client = client        # Discord 클라이언트
        self.channels = channels    # 테스트 채널 딕셔너리
        self.results = []          # 테스트 결과
    
    async def run(self):
        """테스트 실행"""
        pass
    
    async def verify(self):
        """결과 검증"""
        pass
```

## 테스트 케이스별 역할

### test_connection.py
- 봇 시작 확인
- Discord 연결 상태
- 채널 접근 권한
- 초기 데이터 로드

### test_messages.py
- HEARTBEAT 메시지 파싱
- 온라인 상태 업데이트
- 파일 시스템 변경 확인
- 다양한 메시지 형식 테스트

### test_commands.py
- 각 명령어별 개별 테스트
- 응답 시간 측정
- 응답 내용 검증
- 권한 확인

### test_background.py
- 주기적 업데이트 동작
- 오프라인 처리
- 갓팩 검증 프로세스
- 타이머 기반 작업

## 새 테스트 추가 방법

1. `test_새기능.py` 파일 생성
2. 위 구조를 따르는 클래스 작성
3. `__init__.py`에 import 추가
4. test_simulator.py에 등록

## 테스트 작성 팁
- 하나의 테스트는 하나의 기능만
- 실패 원인을 명확히 기록
- 타임아웃 설정 필수
- 예외 처리 철저히