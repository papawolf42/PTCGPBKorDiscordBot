# Poke.py 테스트 실행 가이드

## 완료된 작업

1. **LocalFile.py** - 로컬 파일 시스템 기반 데이터 저장 모듈 구현
2. **LocalFileAdapter.py** - GIST 인터페이스를 LocalFile로 변환하는 어댑터 구현
3. **migrate_to_local.py** - GitHub Gist 데이터를 로컬로 마이그레이션 (6개 파일 성공)
4. **Poke_test.py** - TEST_MODE와 LocalFileAdapter를 사용하는 테스트 버전 생성

## 현재 상태

### 마이그레이션된 데이터
- `data/poke_data/common/`
  - Common_admin.txt (7명의 관리자)
  - Common_member.json (110명의 멤버)
- `data/poke_data/group7/`
  - Group7_online.txt (온라인 사용자)
  - Group7_godpack.json (38개 갓팩)
  - Group7_godpackCode.json (1개 코드)
- `data/poke_data/group8/`
  - Group8_online.txt (온라인 사용자)

### 테스트 실행 방법

1. **테스트 환경 설정 (.env.test 파일 생성)**
   ```bash
   cp .env.test.example .env.test
   # 테스트 채널 ID들을 실제 값으로 수정
   ```

2. **Poke_test.py 실행**
   ```bash
   # 환경변수와 함께 실행
   TEST_MODE=true python Poke_test.py
   
   # 또는 .env.test 파일 사용
   python Poke_test.py --env .env.test
   ```

## 주요 변경사항

1. **TEST_MODE=True일 때**:
   - LocalFileAdapter를 GIST 모듈로 사용
   - 로컬 파일 시스템에서 데이터 읽기/쓰기
   - 네트워크 지연 없음, API 제한 없음

2. **파일명 매핑**:
   - Admin → Common_admin
   - Alliance → Common_member
   - Group7 → Group7_online
   - GodPack7 → Group7_godpack
   - Code7 → Group7_godpackCode

## 테스트 시나리오

1. **기본 동작 확인**
   - 봇이 정상적으로 시작되는지
   - 데이터를 올바르게 읽는지
   - 명령어가 작동하는지

2. **데이터 수정 확인**
   - 관리자 추가/제거
   - 멤버 정보 업데이트
   - 갓팩 상태 변경

3. **동시성 테스트**
   - 여러 명령어 동시 실행
   - 파일 잠금 확인

## 롤백 방법

만약 문제가 발생하면:
1. Poke_test.py 프로세스 중지
2. 기존 Poke.py 계속 사용
3. 데이터는 GitHub Gist에 그대로 유지됨

## 다음 단계

1. 테스트 채널에서 충분한 검증
2. 점진적으로 실제 채널로 확대
3. 안정화 후 Poke.py를 Poke_test.py로 교체