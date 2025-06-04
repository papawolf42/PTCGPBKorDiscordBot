# Poke.py 시뮬레이션 테스트 계획

## 개요
Discord 연결 상태에서 가상의 메시지와 상황을 만들어 Poke.py의 모든 기능을 체계적으로 테스트합니다.

## 테스트 환경 설정

### 1. 테스트 봇 계정
- 테스트 전용 Discord 봇 토큰 사용
- TEST_MODE=true로 실행 (10초 자동 종료)

### 2. 테스트 채널 구성
- Group7_TEST: 테스트 전용 채널 세트
  - TEST_GROUP7_HEARTBEAT_ID
  - TEST_GROUP7_DETECT_ID
  - TEST_GROUP7_POSTING_ID
  - TEST_GROUP7_COMMAND_ID
  - TEST_GROUP7_MUSEUM_ID

### 3. 테스트 데이터 디렉토리
- data_test/poke_data/
  - common/: member.json, admin.txt
  - group7/: online.txt, godpack.json, godpackCode.json

## 단계별 테스트 시나리오

### Phase 1: 기본 연결 및 초기화 (Day 1)
1. **봇 시작 테스트**
   - [ ] TEST_MODE=true로 봇 실행
   - [ ] on_ready 이벤트 로그 확인
   - [ ] 10초 자동 종료 확인

2. **초기 데이터 확인**
   - [ ] member.json 로드 확인
   - [ ] admin.txt 로드 확인
   - [ ] USER_DICT 생성 확인

### Phase 2: 메시지 처리 테스트 (Day 2)
1. **정상 HEARTBEAT 메시지**
   ```
   [온라인 & 대기중]
   나의 팩 선호도: 2P 
   배럭: 피카츄ex★ [178]
   유저: testuser1
   코드: 1234-5678-9012
   ```
   - [ ] on_message 이벤트 트리거
   - [ ] 온라인 상태 업데이트
   - [ ] group7/online.txt 파일 확인

2. **다양한 메시지 형식 테스트**
   - [ ] 3P 선호도 메시지
   - [ ] 5P 선호도 메시지
   - [ ] 배럭 수 변경
   - [ ] 잘못된 형식 메시지 (에러 처리)

3. **멀티 유저 시뮬레이션**
   - [ ] 5명의 다른 사용자 메시지 전송
   - [ ] 온라인 목록 업데이트 확인

### Phase 3: 명령어 테스트 (Day 3)

#### 3.1 일반 명령어
1. **!state 명령어**
   - [ ] COMMAND 채널에서 실행
   - [ ] 온라인/등록 사용자 수 확인
   - [ ] 사용자 목록 출력 확인

2. **!list 명령어**
   - [ ] 친구코드 목록 생성
   - [ ] 복사 가능한 형식 확인

3. **!barracks 명령어**
   - [ ] 배럭 수 정렬 확인
   - [ ] 팩 타입별 그룹화
   - [ ] 총 배럭 수 계산

#### 3.2 갓팩 관련 명령어
1. **!gp 명령어**
   - [ ] 테스트 갓팩 코드 입력
   - [ ] POSTING 채널에 포럼 생성 확인
   - [ ] 중복 코드 거부 테스트

2. **!yet 명령어**
   - [ ] 미검증 갓팩 목록 표시
   - [ ] 최근 Good 갓팩 포함 확인

#### 3.3 관리자 명령어
1. **!add testuser2 2345-6789-0123**
   - [ ] 새 사용자 추가
   - [ ] member.json 업데이트

2. **!delete testuser2 2345-6789-0123**
   - [ ] 사용자 제거
   - [ ] 온라인 목록에서 제거

### Phase 4: 백그라운드 태스크 테스트 (Day 4)

1. **update_periodic 시뮬레이션**
   - [ ] 시간 조작으로 10분 경과 시뮬레이션
   - [ ] 오프라인 처리 확인
   - [ ] 온라인 목록 재생성

2. **verify_periodic 시뮬레이션**
   - [ ] 포럼 반응 시뮬레이션 (👍/👎)
   - [ ] 갓팩 상태 변경 (Yet → Good/Bad)
   - [ ] 오래된 포스트 삭제

### Phase 5: 엣지 케이스 및 에러 처리 (Day 5)

1. **권한 테스트**
   - [ ] 비관리자의 admin 명령어 시도
   - [ ] 잘못된 채널에서 명령어 실행

2. **데이터 일관성**
   - [ ] 파일 손상 시뮬레이션
   - [ ] 네트워크 오류 시뮬레이션
   - [ ] 동시 접근 테스트

3. **성능 테스트**
   - [ ] 100명 동시 온라인 시뮬레이션
   - [ ] 대용량 갓팩 목록 처리
   - [ ] 메모리 사용량 모니터링

## 테스트 도구 및 스크립트

### 1. 메시지 시뮬레이터
```python
# test_message_simulator.py
async def simulate_heartbeat_message(channel, user_data):
    """HEARTBEAT 메시지를 시뮬레이션"""
    message = f"""[온라인 & 대기중]
나의 팩 선호도: {user_data['preference']} 
배럭: {user_data['barrack']} [{user_data['count']}]
유저: {user_data['name']}
코드: {user_data['code']}"""
    await channel.send(message)
```

### 2. 시간 조작 도구
```python
# test_time_manipulator.py
def advance_time(minutes):
    """시스템 시간을 조작하여 백그라운드 태스크 트리거"""
    # 구현 필요
```

### 3. 검증 도구
```python
# test_validator.py
def verify_online_list(expected_users):
    """온라인 목록 파일 검증"""
    # 구현 필요
```

## 성공 기준

- [ ] 모든 기능이 문서화된 대로 동작
- [ ] 에러 발생 시 적절한 처리
- [ ] 데이터 일관성 유지
- [ ] 10초 내 모든 기본 기능 테스트 가능

## 다음 단계

1. 테스트 시뮬레이터 스크립트 작성
2. 각 Phase별 자동화 스크립트 개발
3. 테스트 결과 리포트 자동 생성
4. CI/CD 파이프라인 통합