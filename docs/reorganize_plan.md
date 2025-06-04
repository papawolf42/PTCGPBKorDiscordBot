# 프로젝트 구조 재구성 계획

## 현재 상황
- 루트 디렉토리에 파일들이 너무 많음
- 테스트 파일과 실제 파일이 섞여 있음
- 용도별 구분이 안 되어 있음

## 제안하는 새로운 구조

```
PTCGPBkor/
├── src/                      # 메인 소스 코드
│   ├── bots/                 # 봇 실행 파일들
│   │   ├── Poke.py          # Group7,8 갓팩 봇 (Gist 사용)
│   │   ├── Poke2.py         # 메인 갓팩 봇 (파일 기반)
│   │   ├── Poke20.py        # 20% 팩 봇
│   │   ├── Poke3.py         # 포럼 관리 봇
│   │   └── Poke4.py         # 테스트용 봇
│   │
│   ├── modules/              # 공통 모듈
│   │   ├── GIST.py          # GitHub Gist API
│   │   ├── LocalFile.py     # 로컬 파일 시스템
│   │   ├── LocalFileAdapter.py # GIST 호환 어댑터
│   │   └── GroupInfo.py     # 그룹 정보
│   │
│   └── utils/                # 유틸리티
│       ├── deleteOldPost.py  # 오래된 포스트 삭제
│       └── save_to_obsidian.py # Obsidian 저장
│
├── tests/                    # 테스트 관련
│   ├── Poke_test.py         # Poke.py 테스트 버전
│   ├── Poke_local.py        # Poke.py 로컬 버전
│   ├── test_adapter.py      # 어댑터 테스트
│   ├── test_local_system.py # 로컬 시스템 테스트
│   └── testGPT.py           # GPT 테스트
│
├── scripts/                  # 스크립트 및 도구
│   ├── migrate_to_local.py  # 마이그레이션 스크립트
│   ├── check_gist_data.py   # Gist 데이터 확인
│   └── check_bot_status.py  # 봇 상태 확인
│
├── data/                     # 데이터 디렉토리 (현재 상태 유지)
│   ├── heartbeat_data/
│   ├── user_data/
│   ├── raw/
│   └── poke_data/           # Poke.py용 로컬 데이터
│
├── docs/                     # 문서
│   ├── CLAUDE.md            # 프로젝트 컨텍스트
│   ├── TODO.md              # 할 일 목록
│   ├── run_test.md          # 테스트 실행 가이드
│   ├── architecture.md
│   ├── migration-plan.md
│   ├── analysis.md
│   ├── test-environment.md
│   ├── gist-to-local-migration.md
│   ├── deployment-strategy.md
│   └── system-architecture.md
│
├── config/                   # 설정 파일
│   ├── config.py
│   ├── .env                 # 실제 환경변수
│   ├── .env.test            # 테스트 환경변수
│   └── .env.test.example    # 테스트 환경변수 예시
│
├── logs/                     # 로그 파일
│   └── poke_test.log
│
├── requirements.txt
├── .gitignore
└── README.md                 # 프로젝트 설명 (새로 생성)

## 삭제할 디렉토리/파일
- chatParser/
- hbBackup/
- Testlab/
- obsidian-chat-logger.js
- vip_ids.txt (필요시 data/로 이동)
```

## 실행 계획

### 1단계: 백업
```bash
# 전체 백업
cp -r . ../PTCGPBkor_backup_$(date +%Y%m%d)
```

### 2단계: 디렉토리 생성
```bash
mkdir -p src/{bots,modules,utils}
mkdir -p tests scripts config logs
```

### 3단계: 파일 이동
```bash
# 봇 파일들
mv Poke*.py src/bots/

# 모듈들
mv GIST.py LocalFile*.py GroupInfo.py src/modules/

# 유틸리티
mv deleteOldPost.py save_to_obsidian.py src/utils/

# 테스트
mv test*.py tests/
mv testGPT.py tests/

# 스크립트
mv migrate_to_local.py check_*.py scripts/

# 설정
mv config.py .env* config/

# 문서
mv *.md docs/

# 로그
mv *.log logs/
```

### 4단계: 불필요한 파일 삭제
```bash
rm -rf chatParser hbBackup Testlab
rm obsidian-chat-logger.js
```

### 5단계: import 경로 수정
각 파일의 import 문을 새로운 구조에 맞게 수정 필요

이렇게 정리하면 어떨까요?