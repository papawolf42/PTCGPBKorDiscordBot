# Poke.py: GitHub Gist → 로컬 파일 마이그레이션 계획

## 현재 Gist 사용 현황

### 저장되는 데이터
1. **TEXT 형식 (줄바꿈 구분)**
   - `Group8_Admin`: 관리자 목록
   - `Group8_online`: 온라인 유저 친구 코드

2. **JSON 형식**
   - `Group8_member`: 회원 정보 (사용자별 데이터)
   - `Group8_godpack`: 갓팩 정보 (포스트별 상태)
   - `Group8_godpackCode`: 갓팩 친구 코드 목록

### API 호출 패턴
- **30초마다**: 온라인 유저 확인, 멤버 정보 업데이트
- **120초마다**: 갓팩 상태 확인, 포럼 자동 분류
- **이벤트 발생 시**: 즉시 업데이트

## 마이그레이션 전략

### Phase 1: 준비 작업
1. **로컬 디렉토리 구조**
   ```
   data/
   └── poke_data/
       ├── group7/
       │   ├── admin.txt
       │   ├── online.txt
       │   ├── member.json
       │   ├── godpack.json
       │   └── godpackCode.json
       └── group8/
           ├── admin.txt
           ├── online.txt
           ├── member.json
           ├── godpack.json
           └── godpackCode.json
   ```

2. **LocalFile.py 모듈 작성**
   ```python
   class LocalFile:
       def __init__(self, base_path="data/poke_data"):
           self.base_path = base_path
           
       def uploadFile(self, group, filename, content, format='TEXT'):
           # 로컬 파일로 저장
           
       def openFile(self, group, filename, format='TEXT'):
           # 로컬 파일에서 읽기
   ```

### Phase 2: 테스트 환경 구축
1. **TEST_MODE 플래그 추가**
   ```python
   TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
   
   if TEST_MODE:
       # 테스트 채널만 사용
       ALLOWED_CHANNELS = {...}
       # 로컬 파일 사용
       storage = LocalFile("data_test/poke_data")
   else:
       # 실제 채널 사용
       # Gist 사용 (기존)
       storage = GIST(token)
   ```

2. **데이터 마이그레이션 스크립트**
   ```python
   # migrate_to_local.py
   # 1. Gist에서 모든 데이터 다운로드
   # 2. 로컬 파일로 저장
   # 3. 검증
   ```

### Phase 3: 점진적 전환
1. **이중 저장 모드**
   - 읽기: Gist 실패 시 로컬 파일 폴백
   - 쓰기: Gist와 로컬 파일 동시 저장

2. **모니터링**
   - 데이터 일관성 검증
   - 성능 비교
   - 에러 로그

3. **완전 전환**
   - Gist 의존성 제거
   - 로컬 파일만 사용

## 구현 순서

### 1단계: LocalFile.py 구현
- GIST.py와 동일한 인터페이스
- 파일 읽기/쓰기 기능
- 에러 처리

### 2단계: 테스트 코드 작성
- 단위 테스트
- 통합 테스트
- 부하 테스트

### 3단계: Poke_test.py 생성
- TEST_MODE 적용
- LocalFile 사용
- 테스트 채널에서만 동작

### 4단계: 데이터 마이그레이션
- 백업 생성
- 마이그레이션 실행
- 검증

### 5단계: 라이브 전환
- 점진적 롤아웃
- 모니터링
- 완전 전환

## 예상 효과

### 장점
- **성능**: 네트워크 지연 제거 (API 호출 없음)
- **안정성**: GitHub API 제한 영향 없음
- **비용**: API 사용량 0
- **유연성**: 로컬 파일 직접 수정 가능

### 단점
- **백업**: 수동 백업 필요
- **동기화**: 멀티 인스턴스 시 파일 동기화 필요
- **보안**: 파일 시스템 권한 관리

## 주의사항
1. **파일 잠금**: 동시 쓰기 시 충돌 방지
2. **백업 정책**: 일일 백업 자동화
3. **권한 설정**: 파일 읽기/쓰기 권한
4. **에러 처리**: 파일 손상 시 복구 방안

## 롤백 계획
1. 기존 Poke.py 백업 유지
2. Gist 데이터 보존
3. 즉시 전환 가능한 스크립트 준비