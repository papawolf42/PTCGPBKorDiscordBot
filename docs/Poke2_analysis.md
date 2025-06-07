# Poke2.py 상세 분석 문서

## 📋 개요
Poke2.py는 포켓몬 트레이딩 카드 게임 갓팩(God Pack) 관리를 위한 메인 Discord 봇입니다. Group7을 담당하며, 사용자 모니터링, 친구 목록 자동 생성, 팩 감지 및 포럼 포스팅 등의 핵심 기능을 제공합니다.

## 🏗️ 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                          Poke2.py Bot                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   Discord   │  │   User       │  │   Friend List      │   │
│  │   Events    │  │   Management │  │   Generator        │   │
│  │             │  │              │  │                    │   │
│  │ • on_ready  │  │ • Profile    │  │ • Phase 1 & 2     │   │
│  │ • on_message│  │ • Settings   │  │ • Optimization    │   │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬──────────┘   │
│         │                 │                     │              │
│         └─────────────────┴─────────────────────┘              │
│                           │                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    Data Storage                          │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  📁 heartbeat_data/   📁 user_data/   📁 raw/          │  │
│  │     └─ {user}.json       └─ {user}.json  └─ friend lists│  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   Slash     │  │   Pack       │  │   Background       │   │
│  │   Commands  │  │   Detection  │  │   Tasks            │   │
│  │             │  │              │  │                    │   │
│  │ • /내정보   │  │ • GP Detect  │  │ • Status Check    │   │
│  │ • /목표배럭 │  │ • Forum Post │  │ • Friend Update   │   │
│  │ • /팩선호도 │  │ • Auto Tags  │  │ • Error Handle    │   │
│  │ • /졸업팩   │  │              │  │                    │   │
│  └─────────────┘  └──────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 데이터 흐름도

### 1. Heartbeat 처리 흐름
```
Discord Message (HEARTBEAT Channel)
         │
         ▼
┌─────────────────┐
│ Parse Heartbeat │
│   Message       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│ Extract Data:   │     │ Memory Cache │
│ • Barracks      │────▶│ heartbeat_   │
│ • Version       │     │ records{}    │
│ • Type          │     └──────────────┘
│ • Pack Select   │              │
└────────┬────────┘              │
         │                       ▼
         ▼              ┌──────────────┐
┌─────────────────┐     │ File System  │
│ Update User     │────▶│ heartbeat_   │
│ Profile         │     │ data/{}.json │
└─────────────────┘     └──────────────┘
```

### 2. 친구 목록 생성 흐름
```
┌──────────────────┐
│ Online Users     │
│ Detection        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Calculate Target │
│ Barracks for     │
│ Each User        │
└────────┬─────────┘
         │
    ┌────┴────┐
    │ Phase 1 │
    └────┬────┘
         │
┌──────────────────┐
│ Add friends by   │
│ pack preference  │
│ (non-graduated)  │
└────────┬─────────┘
         │
    ┌────┴────┐
    │ Phase 2 │
    └────┬────┘
         │
┌──────────────────┐
│ Fill remaining   │
│ slots with       │
│ graduated users  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Optimize &       │
│ Balance Lists    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Write to Files:  │
│ • {user}_added_by│
│ • {user}         │
└──────────────────┘
```

### 3. 슬래시 커맨드 처리 흐름
```
User Input (/command)
         │
         ▼
┌──────────────────┐
│ Discord Slash    │
│ Command Handler  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────┐
│ Find User        │────▶│ user_profiles│
│ Profile          │     │ {}           │
└────────┬─────────┘     └──────────────┘
         │
         ▼
┌──────────────────┐
│ Update User      │
│ Settings         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────┐
│ Save to Disk     │────▶│ user_data/   │
│                  │     │ {user}.json  │
└────────┬─────────┘     └──────────────┘
         │
         ▼
┌──────────────────┐
│ Send Response    │
│ (ephemeral)      │
└──────────────────┘
```

## 📊 주요 클래스 및 데이터 구조

### User 클래스
```python
class User:
    def __init__(self, name):
        self.name = name                    # 사용자명
        self.barracks = 0                   # 현재 배럭 수
        self.version = ""                   # 게임 버전
        self.type = ""                      # 사용자 타입
        self.pack_select = ""               # 선택한 팩
        self.code = ""                      # 친구 코드
        self.discord_id = ""                # Discord ID
        self.group_name = ""                # 소속 그룹
        self.custom_target_barracks = None  # 커스텀 목표 배럭
        self.preferred_pack_order = []      # 선호 팩 순서
        self.graduated_packs = []           # 졸업한 팩 목록
```

### 메모리 캐시 구조
```python
# Heartbeat 기록
heartbeat_records = {
    "username": {
        "latest_record": {
            "timestamp": "2025-06-06T12:00:00",
            "barracks": 165,
            "version": "1.0.7",
            "type": "whale",
            "pack_select": "Buzzwole"
        }
    }
}

# 사용자 프로필
user_profiles = {
    "username": User 객체
}
```

## 🎯 핵심 기능 상세

### 1. Heartbeat 모니터링
- **목적**: 사용자의 온라인 상태와 게임 정보 실시간 추적
- **처리 주기**: 메시지 수신 즉시
- **저장 데이터**: 타임스탬프, 배럭 수, 버전, 타입, 선택 팩

### 2. 친구 목록 자동 생성
- **Phase 1**: 졸업하지 않은 팩 기준으로 매칭
- **Phase 2**: 목표 미달 시 졸업 팩 사용자로 채움
- **최적화**: 특정 사용자에게 친구 요청이 집중되지 않도록 분산

### 3. 오류 자동 처리
- **감지 조건**: "already" 메시지 감지
- **처리 방식**: 목표 배럭을 5씩 감소 (최소 100까지)
- **리셋 조건**: 사용자가 스레드에 댓글 작성 시

### 4. 팩 감지 및 포럼 포스팅
- **감지 채널**: DETECT_ID
- **포스팅 위치**: POSTING_ID (포럼 채널)
- **태그 시스템**: Yet, Good, Bad, 1P~5P, Notice

## 🔧 환경 설정

### 필수 환경 변수
```bash
# Discord 관련
DISCORD_BOT_TOKEN=
DISCORD_SERVER_ID=
DISCORD_GROUP7_HEARTBEAT_ID=
DISCORD_GROUP7_DETECT_ID=
DISCORD_GROUP7_POSTING_ID=
DISCORD_GROUP7_COMMAND_ID=
DISCORD_GROUP7_MUSEUM_ID=

# 태그 ID
DISCORD_GROUP7_TAG_YET=
DISCORD_GROUP7_TAG_GOOD=
DISCORD_GROUP7_TAG_BAD=
DISCORD_GROUP7_TAG_1P=
# ... 2P~5P, Notice

# 외부 데이터
PASTEBIN_URL=
```

### 디렉토리 구조
```
data/
├── heartbeat_data/     # 사용자별 heartbeat 기록
│   └── {username}.json
├── user_data/          # 사용자 프로필 정보
│   └── {username}.json
└── raw/                # 생성된 친구 목록
    ├── {username}      # 단순 코드 목록
    └── {username}_added_by  # 상세 정보 포함
```

## 🚀 주요 혁신 기능

### 1. 졸업 팩 시스템
- 사용자가 더 이상 필요 없는 팩을 "졸업"으로 표시
- 친구 매칭 시 졸업 팩은 우선순위에서 제외
- Phase 2에서만 필요시 포함

### 2. 커스텀 목표 배럭
- 기본값: 170
- 사용자별 개별 설정 가능
- 오류 발생 시 자동 조정

### 3. 팩 선호도 시스템
- 최대 4개 팩까지 우선순위 지정
- 미지정 팩은 기본 순서로 자동 채움
- 친구 매칭 시 선호도 반영

### 4. 스레드 기반 피드백
- 사용자가 문제 스레드에 댓글 작성 시 감지
- 목표 배럭 자동 리셋으로 문제 해결

## 📝 개선 가능 사항

1. **데이터베이스 도입**: 현재 파일 기반 → DB로 전환
2. **캐싱 최적화**: Redis 등 활용한 성능 개선
3. **모니터링 대시보드**: 실시간 상태 확인 웹 인터페이스
4. **API 서버**: 다른 봇과의 데이터 공유를 위한 REST API
5. **백업 시스템**: 자동 백업 및 복구 기능