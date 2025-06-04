# 무중단 배포 전략

## 현재 문제점
- 봇 수정 시 재시작 필요 → 서비스 중단
- 라이브 환경에서 직접 테스트 → 버그 위험
- 수동 롤백 → 복구 시간 지연

## 해결 방안

### 1. Blue-Green 배포 방식
```
현재 실행 중 (Blue)    →    새 버전 준비 (Green)
     Poke.py                    Poke_new.py
        ↓                           ↓
   Discord API  ←─────────────→  Discord API
                  동시 연결
```

**구현 방법:**
```bash
# 새 버전을 다른 이름으로 실행
cp Poke.py Poke_new.py
# 수정 작업
# 새 버전 실행 (동일한 봇 토큰 사용)
python Poke_new.py

# 안정화 확인 후 기존 버전 종료
pkill -f Poke.py
mv Poke_new.py Poke.py
```

### 2. 프로세스 관리자 사용 (PM2)

```bash
# PM2 설치
npm install -g pm2

# ecosystem.config.js 생성
module.exports = {
  apps: [{
    name: 'Poke',
    script: 'Poke.py',
    interpreter: 'python3',
    watch: false,
    instances: 1,
    max_restarts: 3,
    restart_delay: 5000
  }, {
    name: 'Poke2',
    script: 'Poke2.py',
    interpreter: 'python3',
    watch: false,
    instances: 1
  }, {
    name: 'Poke20',
    script: 'Poke20.py',
    interpreter: 'python3',
    watch: false,
    instances: 1
  }]
};
```

**사용법:**
```bash
# 모든 봇 시작
pm2 start ecosystem.config.js

# 무중단 재시작
pm2 reload Poke2

# 상태 확인
pm2 status

# 로그 확인
pm2 logs Poke2
```

### 3. 기능 플래그 (Feature Flags)

```python
# config.py
FEATURES = {
    'new_pack_detection': False,  # 새 팩 감지 기능
    'improved_heartbeat': False,   # 개선된 하트비트
    'group_limit_10': False        # 10명 제한 기능
}

# Poke20.py에서
from config import FEATURES

if FEATURES['group_limit_10']:
    # 새 로직
    MAX_USERS_PER_GROUP = 10
else:
    # 기존 로직
    MAX_USERS_PER_GROUP = 999
```

### 4. 카나리 배포

특정 그룹에서만 새 기능 테스트:
```python
# 특정 그룹에서만 새 기능 활성화
CANARY_GROUPS = ['Group1']  # 테스트 그룹

if message.guild.name in CANARY_GROUPS:
    # 새 기능 사용
    await new_feature_handler(message)
else:
    # 기존 기능 사용
    await legacy_handler(message)
```

### 5. 자동 롤백 시스템

```python
# health_check.py
import asyncio
import discord
from datetime import datetime, timedelta

class HealthMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.error_count = 0
        self.last_heartbeat = datetime.now()
        
    async def check_health(self):
        while True:
            try:
                # 핵심 기능 테스트
                if not await self.check_heartbeat():
                    self.error_count += 1
                    
                if self.error_count > 5:
                    await self.trigger_rollback()
                    
            except Exception as e:
                print(f"Health check failed: {e}")
                
            await asyncio.sleep(60)  # 1분마다 체크
    
    async def trigger_rollback(self):
        # 자동 롤백 실행
        os.system("./rollback.sh")
```

### 6. 롤백 스크립트

```bash
#!/bin/bash
# rollback.sh

# 백업 버전으로 복원
cp backup/Poke2_stable.py Poke2.py

# PM2로 재시작
pm2 restart Poke2

# 알림 전송
curl -X POST https://discord.webhook.url \
  -H "Content-Type: application/json" \
  -d '{"content": "⚠️ Poke2 자동 롤백 실행됨"}'
```

## 권장 구현 순서

1. **즉시 적용 가능**: PM2 도입
   - 설치 간단, 즉시 효과
   - 로그 관리, 자동 재시작

2. **단기 (1주)**: 기능 플래그
   - 코드 수정 최소화
   - 안전한 기능 테스트

3. **중기 (2-3주)**: Blue-Green 배포
   - 무중단 업데이트
   - 빠른 롤백

4. **장기 (1개월)**: 완전 자동화
   - 헬스체크
   - 자동 롤백
   - 모니터링 대시보드

## 테스트 환경 구축

```python
# test_config.py
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

if TEST_MODE:
    # 테스트 서버 ID 사용
    GUILD_IDS = [1234567890]  # 테스트 서버
    BOT_TOKEN = os.getenv('TEST_BOT_TOKEN')
else:
    # 실제 서버 ID
    GUILD_IDS = [실제서버ID들]
    BOT_TOKEN = os.getenv('BOT_TOKEN')
```

이렇게 하면 라이브 서비스 영향 없이 안전하게 개발하고 배포할 수 있습니다.