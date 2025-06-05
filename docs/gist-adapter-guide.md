# GISTAdapter 구조 및 사용법 가이드

## 개요
GISTAdapter는 GitHub Gist API를 사용하는 GIST.py의 인터페이스를 그대로 유지하면서, 실제로는 로컬 파일 시스템을 사용하도록 만든 어댑터 패턴 구현체입니다.

## 주요 차이점

### GIST.py (원본)
- **저장소**: GitHub Gist (클라우드)
- **API**: GitHub REST API 사용
- **인증**: GitHub 토큰 필요
- **장점**: 여러 인스턴스에서 실시간 동기화
- **단점**: API 제한, 네트워크 의존성

### GISTAdapter.py (어댑터)
- **저장소**: 로컬 파일 시스템
- **API**: 파일 I/O
- **인증**: 불필요
- **장점**: 빠른 속도, 오프라인 작동
- **단점**: 인스턴스 간 동기화 없음

## 클래스 구조 비교

```
GIST.py                          GISTAdapter.py
───────────────────────────────────────────────────────────────
FILE (기본 클래스)               (해당 없음 - 어댑터가 대체)
├─ TEXT                         TextAdapter
│  └─ self.DATA = set()        └─ self.DATA = set()
└─ JSON                         JsonAdapter
   └─ self.DATA = {}              └─ self.DATA = {}

SERVER                          SERVER (GIST.py 것 그대로 사용)
USER                            USER (GIST.py 것 그대로 사용)
```

## 메서드 비교

### 1. 초기화

#### GIST.py
```python
# GitHub API 정보로 초기화
Group7 = GIST.TEXT(GIST_ID, "Group7", initial=True)
# GIST_ID: GitHub Gist의 고유 ID
# "Group7": Gist 내의 파일명
# initial: True면 즉시 데이터 로드
```

#### GISTAdapter.py
```python
# 파일 경로 매핑으로 변환
Group7 = GIST.TEXT(GIST_ID, "Group7", initial=True)
# GIST_ID는 무시됨 (호환성을 위해 받기만 함)
# "Group7" → "group7/online.txt"로 매핑
# 실제 경로: data/poke_data/group7/online.txt
```

### 2. 데이터 로드

#### GIST.py
```python
def fetch_data(self):
    # 1. GitHub API로 raw URL 가져오기
    # 2. raw URL에서 콘텐츠 다운로드
    # 3. 텍스트를 set으로 변환
    return set(data.splitlines())
```

#### GISTAdapter.py
```python
def load(self):
    # 1. 로컬 파일 읽기
    # 2. 텍스트를 set으로 변환
    self.DATA = set(content.split('\n'))
```

### 3. 데이터 수정

#### GIST.py
```python
def edit(self, mode, text):
    if mode == '+':
        self.DATA.add(text)      # 메모리에만 추가
    elif mode == '-':
        self.DATA.discard(text)  # 메모리에서만 제거
    # update() 호출 전까지는 Gist에 반영 안됨
```

#### GISTAdapter.py
```python
def edit(self, mode, text):
    if mode == '+':
        self.DATA.add(text)      # 동일하게 메모리에만
    elif mode == '-':
        self.DATA.discard(text)  # 동일하게 메모리에서만
    # update() 호출 전까지는 파일에 반영 안됨
```

### 4. 저장

#### GIST.py
```python
def update(self):
    # GitHub API PATCH 요청
    # 전체 파일 내용을 업로드
    response = requests.patch(self.API, json=data, headers=headers)
```

#### GISTAdapter.py
```python
def update(self):
    # 로컬 파일에 쓰기
    with open(self.file_path, 'w') as f:
        f.write('\n'.join(sorted(self.DATA)))
```

## 파일 매핑 규칙

### TEXT 파일 매핑
```python
mapping = {
    "Admin": ("common", "admin.txt"),
    "Group7": ("group7", "online.txt"),
    "Group8": ("group8", "online.txt"),
    "GroupTest": ("test", "online.txt"),  # TEST_MODE
}
```

### JSON 파일 매핑
```python
mapping = {
    "Alliance": ("common", "member.json"),
    "GodPack7": ("group7", "godpack.json"),
    "Code7": ("group7", "godpackCode.json"),
    "GodPack8": ("group8", "godpack.json"),
    "Code8": ("group8", "godpackCode.json"),
    "GodPackTest": ("test", "godpack.json"),  # TEST_MODE
    "CodeTest": ("test", "godpackCode.json"),  # TEST_MODE
}
```

## 디렉토리 구조
```
data/poke_data/           (일반 모드)
data_test/poke_data/      (TEST_MODE)
├── common/
│   ├── admin.txt         # 관리자 목록
│   └── member.json       # 멤버 정보 (이름: 코드)
├── group7/
│   ├── online.txt        # 온라인 사용자 코드 목록
│   ├── godpack.json      # 갓팩 정보
│   └── godpackCode.json  # 갓팩 검증 코드
├── group8/
│   └── (group7과 동일)
└── test/                 # TEST_MODE 전용
    └── (group7과 동일)
```

## 사용 예시

### 1. 온라인 사용자 추가
```python
# Poke.py에서
Server.FILE.edit('+', '1234-5678-9012')  # 메모리에 추가
Server.FILE.update()                      # 파일에 저장

# 실제 동작 (GISTAdapter)
# 1. TextAdapter.edit('+', '1234-5678-9012')
# 2. self.DATA.add('1234-5678-9012')
# 3. TextAdapter.update()
# 4. data/poke_data/group7/online.txt에 저장
```

### 2. 갓팩 정보 저장
```python
# Poke.py에서
Server.GODPACK.edit('+', '2024.12.19 papawolf 100% 5P', 'Yet')
Server.GODPACK.update()

# 실제 동작 (GISTAdapter)
# 1. JsonAdapter.edit('+', key, value)
# 2. self.DATA[key] = value
# 3. JsonAdapter.update()
# 4. data/poke_data/group7/godpack.json에 저장
```

## 주의사항

### 1. 봇 재시작 시 동작 차이
- **GIST**: 메모리가 비어있음 → `recent_online()`이 모든 사용자 재등록
- **GISTAdapter**: 파일이 유지됨 → `recent_online()`이 기존 사용자 건너뜀
- **결과**: Server.ONLINE이 비어있어 타임아웃 체크 작동 안함

### 2. 파일 동기화
- **GIST**: 여러 봇이 같은 Gist 사용 시 자동 동기화
- **GISTAdapter**: 각 봇이 독립적인 파일 사용

### 3. 성능
- **GIST**: 네트워크 지연, API 제한 (시간당 5000회)
- **GISTAdapter**: 즉각적인 파일 I/O, 제한 없음

## 마이그레이션 가이드

### Poke.py에서 전환하기
```python
# 변경 전
import src.modules.GIST as GIST

# 변경 후
import src.modules.GISTAdapter as GIST
# 나머지 코드는 변경 없음!
```

### 데이터 마이그레이션
```bash
# scripts/migration/migrate_to_local.py 실행
python scripts/migration/migrate_to_local.py
```

## 디버깅 팁

### 1. 파일 위치 확인
```python
# TextAdapter/JsonAdapter 내부
print(f"파일 경로: {self.file_path}")
# 출력: data/poke_data/group7/online.txt
```

### 2. 데이터 상태 확인
```python
# 메모리 상태
print(f"Server.ONLINE: {len(Server.ONLINE)}")
print(f"Server.FILE.DATA: {len(Server.FILE.DATA)}")

# 파일 상태
with open('data/poke_data/group7/online.txt') as f:
    print(f"파일 내용: {len(f.read().splitlines())}개")
```

### 3. TEST_MODE 확인
```python
# GISTAdapter가 올바른 경로 사용하는지
print(f"Base path: {GIST._adapter.local_storage.base_path}")
# TEST_MODE: /path/to/data_test/poke_data
# 일반: /path/to/data/poke_data
```

## 향후 개선 사항
1. 파일 잠금(locking) 메커니즘 추가
2. 백업 기능 추가
3. 파일 변경 감지 기능
4. 인스턴스 간 동기화 옵션

## 시각적 구조 설명

### 1. 전체 아키텍처
```
┌─────────────────────────────────────────────────────────────────┐
│                           Poke.py                                │
│  import src.modules.GISTAdapter as GIST                         │
│  Group7 = GIST.TEXT(ID, "Group7", False)                       │
│  Member = GIST.JSON(ID, "Alliance")                            │
└────────────────────────┬───────────────────────────────────────┘
                         │ 호출
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      GISTAdapter 모듈                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ _adapter = GISTAdapter()  # 싱글톤 인스턴스                  │ │
│ │                                                              │ │
│ │ TEXT = _adapter.TEXT      # 함수 참조                       │ │
│ │ JSON = _adapter.JSON      # 함수 참조                       │ │
│ │ SERVER = SERVER           # 클래스 직접 노출                │ │
│ │ USER = USER               # 클래스 직접 노출                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2. GISTAdapter 내부 구조
```
┌─────────────────────────────────────────────────────────────────┐
│                      GISTAdapter 클래스                          │
├─────────────────────────────────────────────────────────────────┤
│ __init__(self):                                                 │
│   ┌───────────────────────────────────────────┐                │
│   │ TEST_MODE 확인                             │                │
│   │   ↓ Yes              ↓ No                 │                │
│   │ data_test/         data/                  │                │
│   │ poke_data/         poke_data/             │                │
│   └───────────────────────────────────────────┘                │
│   self.local_storage = LocalFile(base_path)                     │
│                                                                  │
│ TEXT(gist_id, filename, initial):                               │
│   ┌───────────────────────────────────────────┐                │
│   │ 매핑 테이블:                               │                │
│   │ "Group7" → ("group7", "online.txt")       │                │
│   │ "GroupTest" → ("test", "online.txt")      │                │
│   └───────────────────────────────────────────┘                │
│   return TextAdapter(folder, filename)                          │
│                                                                  │
│ JSON(gist_id, filename):                                        │
│   ┌───────────────────────────────────────────┐                │
│   │ 매핑 테이블:                               │                │
│   │ "Alliance" → ("common", "member.json")    │                │
│   │ "GodPack7" → ("group7", "godpack.json")   │                │
│   └───────────────────────────────────────────┘                │
│   return JsonAdapter(folder, filename)                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Adapter 클래스 구조
```
┌─────────────────────────────────────────────────────────────────┐
│                        TextAdapter                               │
├─────────────────────────────────────────────────────────────────┤
│ 속성:                                                            │
│ • self.DATA = set()          # {"1234-5678", "2345-6789"}      │
│ • self.NAME = "Group7"       # GIST 호환성                      │
│ • self.file_path = "/full/path/to/online.txt"                  │
│                                                                  │
│ 메서드:                                                          │
│ • load()     → 파일 읽기 → self.DATA 업데이트                  │
│ • edit('+', code) → self.DATA.add(code)                        │
│ • edit('-', code) → self.DATA.discard(code)                    │
│ • update()   → self.DATA → 파일 쓰기                           │
│ • fetch_raw() → load() 후 self.DATA 반환                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        JsonAdapter                               │
├─────────────────────────────────────────────────────────────────┤
│ 속성:                                                            │
│ • self.DATA = {}             # {"key": "value", ...}           │
│ • self.NAME = "Alliance"     # GIST 호환성                      │
│ • self.file_path = "/full/path/to/member.json"                 │
│                                                                  │
│ 메서드:                                                          │
│ • load()     → JSON 파일 읽기 → self.DATA 업데이트             │
│ • edit('+', key, value) → self.DATA[key] = value               │
│ • edit('-', key) → self.DATA.pop(key)                          │
│ • update()   → self.DATA → JSON 파일 쓰기                      │
│ • fetch_raw() → load() 후 self.DATA 반환                       │
└─────────────────────────────────────────────────────────────────┘
```

### 4. 데이터 흐름도 - 사용자 로그인 예시
```
사용자가 Heartbeat 메시지 전송
            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Poke.py: on_message 이벤트                                      │
│   USER_DICT[name].online(Server)                                │
└────────────────────────┬───────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ USER.online(Server) 메서드                                      │
│   Server.FILE.edit('+', self.CODE)                              │
│   Server.WAITING.add(self)                                      │
└────────────────────────┬───────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ TextAdapter.edit('+', '1234-5678-9012')                        │
│   self.DATA.add('1234-5678-9012')  # 메모리에만                │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ do_update() - 30초 후 (5초 in TEST_MODE)                       │
│   Server.FILE.update()                                          │
└────────────────────────┬───────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ TextAdapter.update()                                            │
│   파일 쓰기: data_test/poke_data/test/online.txt               │
│   내용: "1234-5678-9012\n2345-6789-0123\n..."                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5. GIST vs GISTAdapter 비교
```
GIST.py (원본)                    GISTAdapter.py
┌─────────────────────┐          ┌─────────────────────┐
│ Group7.edit('+',    │          │ Group7.edit('+',    │
│   '1234-5678')      │          │   '1234-5678')      │
└──────────┬──────────┘          └──────────┬──────────┘
           ↓                                  ↓
┌─────────────────────┐          ┌─────────────────────┐
│ self.DATA.add()     │          │ self.DATA.add()     │
│ (메모리)            │          │ (메모리)            │
└──────────┬──────────┘          └──────────┬──────────┘
           ↓                                  ↓
┌─────────────────────┐          ┌─────────────────────┐
│ update() 호출 시:   │          │ update() 호출 시:   │
│                     │          │                     │
│ GitHub API PATCH    │          │ with open(...) as f:│
│ 전체 파일 업로드    │          │   f.write(...)      │
│ (네트워크)          │          │ (로컬 파일)         │
└─────────────────────┘          └─────────────────────┘
```

### 6. 파일 시스템 레이아웃
```
프로젝트 루트/
├── data/                    # 일반 모드
│   └── poke_data/
│       ├── common/
│       │   ├── admin.txt    ← Admin = GIST.TEXT(ID, "Admin")
│       │   └── member.json  ← Alliance = GIST.JSON(ID, "Alliance")
│       ├── group7/
│       │   ├── online.txt   ← Group7 = GIST.TEXT(ID, "Group7")
│       │   └── godpack.json ← GodPack7 = GIST.JSON(ID, "GodPack7")
│       └── group8/
│           └── ...
│
└── data_test/               # TEST_MODE
    └── poke_data/
        ├── common/
        │   └── member.json
        └── test/
            ├── online.txt   ← GroupTest = GIST.TEXT(ID, "GroupTest")
            └── godpack.json ← GodPackTest = GIST.JSON(ID, "GodPackTest")
```

### 7. 메서드 호출 체인
```
Poke.py                     GISTAdapter                 파일 시스템
───────────────────────────────────────────────────────────────────
                                                        
GIST.TEXT() ─────────→ _adapter.TEXT() ────────→ TextAdapter 생성
                              │                           │
                              ↓                           ↓
                       매핑 테이블 조회              파일 경로 결정
                       "Group7" → group7/              │
                       "online.txt"                    ↓
                                                   load() 실행
                                                   파일 → DATA

Group7.edit() ────────→ TextAdapter.edit() ────→ self.DATA 수정
                                                  (메모리만)

Group7.update() ──────→ TextAdapter.update() ──→ 파일에 쓰기
                                                  DATA → 파일

Group7.fetch_raw() ───→ TextAdapter.load() ────→ 파일 다시 읽기
                        + return self.DATA        최신 데이터 반환
```

## Poke.py 워크플로우 기반 이해

### 시나리오 1: 봇 시작 시
```
【GIST 사용 시】
┌─────────────────────────────────────────────────────────────────┐
│ 1. Poke.py 시작                                                 │
│    Group7 = GIST.TEXT(ID, "Group7", False)                     │
└────────────────────────┬───────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. GIST가 GitHub에서 데이터 가져오기                            │
│    • GitHub API 호출                                            │
│    • "Group7" 파일 다운로드                                     │
│    • self.DATA = set() (비어있음 - False로 초기화했으므로)      │
└────────────────────────┬───────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. 온라인 사용자 목록                                           │
│    Server.FILE.DATA = {} (비어있음)                             │
│    Server.ONLINE = {} (비어있음)                                │
└─────────────────────────────────────────────────────────────────┘

【GISTAdapter 사용 시】
┌─────────────────────────────────────────────────────────────────┐
│ 1. Poke.py 시작                                                 │
│    Group7 = GIST.TEXT(ID, "Group7", False)                     │
└────────────────────────┬───────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. GISTAdapter가 로컬 파일 읽기                                 │
│    • "Group7" → "group7/online.txt" 매핑                       │
│    • data/poke_data/group7/online.txt 읽기                     │
│    • self.DATA = {"1234-5678", "2345-6789"} (이미 있던 데이터) │
└────────────────────────┬───────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. 온라인 사용자 목록                                           │
│    Server.FILE.DATA = {"1234-5678", "2345-6789"} (파일 데이터) │
│    Server.ONLINE = {} (❌ 비어있음 - 문제!)                    │
└─────────────────────────────────────────────────────────────────┘
```

### 시나리오 2: 사용자가 로그인할 때 (Heartbeat 메시지)
```
papawolf가 Heartbeat 채널에 메시지 전송
┌─────────────────────────────────────────┐
│ papawolf                                │
│ Online: 1, 2, 3, 4                     │
│ Time: 0m | Packs: 0                   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Poke.py의 처리 과정                           │
├─────────────────────────────────────────────────────────────────┤
│ 1. on_message 이벤트 발생                                       │
│    if "Online:" in message.content:                            │
│       name = "papawolf"                                         │
│                                                                 │
│ 2. 사용자 확인                                                  │
│    if name in USER_DICT.keys():  # papawolf 있음              │
│       USER_DICT["papawolf"].CODE = "1234-5678-9012"           │
│                                                                 │
│ 3. 온라인 처리                                                  │
│    if USER_DICT[name].CODE not in Server.FILE.DATA:           │
│       # 파일에 없으면 추가                                     │
│       USER_DICT[name].online(Server)                          │
└─────────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                  USER.online(Server) 메서드                      │
├─────────────────────────────────────────────────────────────────┤
│ def online(self, Server):                                       │
│     Server.FILE.edit('+', self.CODE)  # "1234-5678-9012" 추가  │
│     Server.WAITING.add(self)          # 대기 목록에 추가       │
└─────────────────────────────────────────────────────────────────┘
                    ↓
【GIST】                           【GISTAdapter】
┌───────────────────────┐        ┌────────────────────────────────┐
│ Server.FILE.edit()    │        │ TextAdapter.edit()             │
│ • 메모리에만 추가     │        │ • 메모리에만 추가              │
│ • DATA.add("1234...")│        │ • DATA.add("1234...")         │
└───────────────────────┘        └────────────────────────────────┘
                    ↓
            30초 후 (TEST_MODE는 5초)
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    do_update() 실행                              │
├─────────────────────────────────────────────────────────────────┤
│ for ID, Server in SERVER_DICT.items():                         │
│     # WAITING에서 ONLINE으로 이동                               │
│     RAW_GIST_DICT[ID] = Server.FILE.fetch_raw()               │
│     for user in Server.WAITING:                                │
│         if user.CODE in RAW_GIST_DICT[ID]:                    │
│             Server.ONLINE.add(user)  # 드디어 ONLINE에 추가!  │
│             "GIST에 업데이트 되었습니다!"                      │
└─────────────────────────────────────────────────────────────────┘
                    ↓
【GIST】                           【GISTAdapter】
┌───────────────────────┐        ┌────────────────────────────────┐
│ Server.FILE.update()  │        │ TextAdapter.update()           │
│ • GitHub API 호출     │        │ • 파일에 쓰기                  │
│ • 네트워크 전송       │        │ • online.txt 업데이트          │
└───────────────────────┘        └────────────────────────────────┘
```

### 시나리오 3: 타임아웃으로 로그아웃
```
┌─────────────────────────────────────────────────────────────────┐
│                  15분(TEST: 10초) 동안 메시지 없음               │
└─────────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│             do_update() - 5초마다 실행 (TEST_MODE)              │
├─────────────────────────────────────────────────────────────────┤
│ # 타임아웃 체크                                                 │
│ now = datetime.now(timezone.utc)                               │
│ timeout = timedelta(seconds=10)  # TEST_MODE                   │
│                                                                 │
│ for user in Server.ONLINE:                                     │
│     if now - user.inform[Server.ID]['TIME'] >= timeout:       │
│         remove.append(user)                                    │
│                                                                 │
│ for user in remove:                                            │
│     user.offline(Server)                                       │
└─────────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                   USER.offline(Server) 메서드                    │
├─────────────────────────────────────────────────────────────────┤
│ def offline(self, Server):                                      │
│     Server.FILE.edit('-', self.CODE)  # 파일에서 제거          │
│     Server.ONLINE.discard(self)       # ONLINE에서 제거        │
│     self.off[Server.ID] = ...         # 오프라인 정보 저장     │
└─────────────────────────────────────────────────────────────────┘
                    ↓
【GIST】                           【GISTAdapter】
┌───────────────────────┐        ┌────────────────────────────────┐
│ Server.FILE.update()  │        │ TextAdapter.update()           │
│ • GitHub에서 제거     │        │ • online.txt에서 제거          │
│ • "1234-5678" 삭제    │        │ • "1234-5678" 라인 삭제        │
└───────────────────────┘        └────────────────────────────────┘
```

### 핵심 차이점 요약
```
┌─────────────────────────────────────────────────────────────────┐
│                        데이터 저장 위치                          │
├─────────────────────────────────────────────────────────────────┤
│ GIST:                                                           │
│ • 인터넷 (GitHub)     ☁️                                       │
│ • 여러 봇이 공유 가능                                          │
│ • 느림 (네트워크)                                              │
│                                                                 │
│ GISTAdapter:                                                    │
│ • 내 컴퓨터 (로컬)    💾                                       │
│ • 이 봇만 사용                                                 │
│ • 빠름 (파일)                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          봇 재시작 시                           │
├─────────────────────────────────────────────────────────────────┤
│ GIST:                                                           │
│ • 모든 데이터가 GitHub에 있음                                   │
│ • 봇이 다시 시작해도 데이터 유지                               │
│ • 하지만 메모리(Server.ONLINE)는 비어있음                      │
│                                                                 │
│ GISTAdapter:                                                    │
│ • 모든 데이터가 파일에 있음                                     │
│ • 봇이 다시 시작해도 데이터 유지                               │
│ • 하지만 메모리(Server.ONLINE)는 비어있음 (동일한 문제!)       │
└─────────────────────────────────────────────────────────────────┘
```

### 왜 GISTAdapter를 만들었나?
```
┌─────────────────────────────────────────────────────────────────┐
│ GIST의 문제점:                                                   │
│ • GitHub API 제한 (시간당 5000회)                               │
│ • 인터넷 연결 필요                                              │
│ • 느린 속도                                                     │
│                                                                  │
│ GISTAdapter의 장점:                                             │
│ • API 제한 없음                                                 │
│ • 오프라인 작동                                                │
│ • 빠른 속도                                                     │
│ • Poke.py 코드 변경 최소화 (import 한 줄만!)                   │
└─────────────────────────────────────────────────────────────────┘
```