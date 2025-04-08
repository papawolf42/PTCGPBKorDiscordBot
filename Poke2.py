import discord
import asyncio
from datetime import datetime, timezone, timedelta
import json
import os
import re
import shutil

# --- 상수 정의 ---
GROUP1_CHANNEL_ID = os.getenv('DISCORD_GROUP1_HEARTBEAT_ID')
GROUP3_CHANNEL_ID = os.getenv('DISCORD_GROUP3_HEARTBEAT_ID')
TARGET_CHANNEL_IDS = {GROUP1_CHANNEL_ID: "Group1", GROUP3_CHANNEL_ID: "Group3"}
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN') # 봇 토큰
HEARTBEAT_DATA_DIR = "data/heartbeat_data" # 데이터 저장 폴더

# --- 봇 설정 ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True # 히스토리 조회에 필요할 수 있음
bot = discord.Client(intents=intents)

# --- 전역 변수 ---
# 사용자별 최신 heartbeat 기록 (메모리): {user_name: {"latest_record": dict, "channel_id_str": str}}
heartbeat_records = {}

# --- 데이터 처리 함수 ---
def ensure_data_dir():
    """데이터 저장 디렉토리 확인 및 생성"""
    if not os.path.exists(HEARTBEAT_DATA_DIR):
        try:
            os.makedirs(HEARTBEAT_DATA_DIR)
            print(f"📁 데이터 디렉토리 생성: {HEARTBEAT_DATA_DIR}")
        except OSError as e:
            print(f"❌ 데이터 디렉토리 생성 실패: {e}")
            raise # 심각한 오류 시 종료

def sanitize_filename(name):
    """사용자 이름을 안전한 파일명으로 변환"""
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    return name[:100] # 100자 제한

def get_user_filepath(user_name):
    """사용자 JSON 파일 경로 반환"""
    return os.path.join(HEARTBEAT_DATA_DIR, f"{sanitize_filename(user_name)}.json")

def read_user_data(user_name):
    """사용자 JSON 파일 읽기 (없거나 오류 시 빈 리스트 반환)"""
    filepath = get_user_filepath(user_name)
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            # 간단한 유효성 검사 및 정렬
            valid_data = [r for r in data if isinstance(r, dict) and 'timestamp' in r]
            valid_data.sort(key=lambda x: x.get('timestamp', ''))
            return valid_data
        else:
            print(f"⚠️ 사용자 '{user_name}' 파일 형식이 리스트가 아님: {filepath}. 빈 리스트 반환.")
            return []
    except (json.JSONDecodeError, Exception) as e:
        print(f"❌ 사용자 '{user_name}' 파일 읽기/디코딩 오류: {e}. 빈 리스트 반환.")
        return []

def write_user_data(user_name, data_list):
    """사용자 기록 리스트를 JSON 파일에 쓰기 (정렬 포함)"""
    filepath = get_user_filepath(user_name)
    try:
        data_list.sort(key=lambda x: x.get('timestamp', '')) # 쓰기 전 정렬 보장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ 사용자 '{user_name}' 파일 쓰기 오류: {e}")
        return False

def load_all_latest_user_data():
    """모든 사용자 파일의 최신 기록을 메모리에 로드"""
    global heartbeat_records
    ensure_data_dir()
    print(f"💾 데이터 폴더 스캔 및 최신 기록 로드 시작: {HEARTBEAT_DATA_DIR}")
    loaded_records = {}
    try:
        for filename in os.listdir(HEARTBEAT_DATA_DIR):
            if filename.endswith(".json"):
                user_name_from_file = filename[:-5] # .json 제거
                user_data = read_user_data(user_name_from_file) # 정렬된 리스트 반환
                if user_data:
                    latest_record = user_data[-1] # 마지막 항목이 최신
                    channel_id_str = latest_record.get('channel_id_str')
                    if channel_id_str:
                         loaded_records[user_name_from_file] = {"latest_record": latest_record, "channel_id_str": channel_id_str}
                    # else: # channel_id_str 없는 경우 경고 제거 (간결화)
                    #     pass
    except Exception as e:
        print(f"❌ 최신 기록 로드 중 오류 발생: {e}")

    heartbeat_records = loaded_records
    print(f"✅ 최신 기록 로드 완료: {len(heartbeat_records)}명")

def parse_heartbeat_message(content):
    """메시지 내용에서 heartbeat 정보 추출"""
    data = {'barracks': 0, 'version': 'Unknown', 'type': 'Unknown', 'select': 'Unknown'}
    online_line = next((line.strip() for line in content.splitlines() if line.strip().lower().startswith("online:")), None)
    if online_line:
        numbers_in_line = re.findall(r'\b\d+\b', online_line)
        data['barracks'] = len(numbers_in_line)

    version_match = re.search(r"^Version:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    if version_match: data['version'] = version_match.group(1).strip()
    type_match = re.search(r"^Type:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    if type_match: data['type'] = type_match.group(1).strip()
    select_match = re.search(r"^Select:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    if select_match: data['select'] = select_match.group(1).strip()
    return data

async def process_heartbeat_message(message, channel_id_str, channel_name):
    """Heartbeat 메시지 처리 (파일 저장 및 메모리 업데이트)"""
    if "Online:" not in message.content: return False # Heartbeat 아니면 처리 안 함

    try:
        user_name = message.content.split("\n")[0].strip()
        if not user_name: return False # 사용자 이름 없으면 스킵

        timestamp_dt = message.created_at.replace(tzinfo=timezone.utc) # UTC 명시
        timestamp_iso = timestamp_dt.isoformat()
        parsed_data = parse_heartbeat_message(message.content)
        parsed_data['channel_id_str'] = channel_id_str # 채널 ID 추가

        recent_record = {"timestamp": timestamp_iso, **parsed_data}

        user_data = read_user_data(user_name) # 기존 기록 읽기

        # 중복 타임스탬프 확인 (중복 시 처리 안 함)
        if any(record.get('timestamp') == timestamp_iso for record in user_data):
            return False

        user_data.append(recent_record) # 새 기록 추가
        if write_user_data(user_name, user_data): # 파일 쓰기 (성공 시)
            print(f"💾 Heartbeat 기록됨 [{channel_name}]: {user_name} ({parsed_data['barracks']} barracks) at {timestamp_iso}")
            heartbeat_records[user_name] = {"latest_record": recent_record, "channel_id_str": channel_id_str} # 메모리 업데이트
            return True # 변경사항 있음
        else:
            return False # 파일 쓰기 실패
    except Exception as e:
        print(f"❌ [{channel_name}] Heartbeat 처리 오류: {e} | 메시지: {message.content[:100]}...")
        return False # 오류 발생 시 변경 없음

# --- 이벤트 핸들러 및 주기적 작업 ---
@bot.event
async def on_ready():
    """봇 준비 완료 시 실행"""
    print(f'✅ 로그인됨: {bot.user}')
    ensure_data_dir()
    print("💾 데이터 로딩 시작...")
    load_all_latest_user_data()

    # 전체 기록 중 마지막 타임스탬프 찾기
    overall_latest_timestamp = None
    if heartbeat_records:
        timestamps = [
            datetime.fromisoformat(data["latest_record"]['timestamp'].replace('Z', '+00:00'))
            for data in heartbeat_records.values()
            if data.get("latest_record") and 'timestamp' in data["latest_record"]
        ]
        if timestamps:
            overall_latest_timestamp = max(timestamps)

    if overall_latest_timestamp:
        print(f"🔄 마지막 기록 시간 ({overall_latest_timestamp.isoformat()}) 이후 메시지 스캔")
    else:
        print("🔄 저장된 기록 없음. 전체 채널 히스토리 스캔 (시간 소요 가능)...")

    history_processed_count = 0
    for channel_id, channel_name in TARGET_CHANNEL_IDS.items():
        channel_id_str = str(channel_id)
        scan_type = '누락분만' if overall_latest_timestamp else '전체'
        print(f"  [{channel_name}] 채널 기록 조회 중... ({scan_type})")
        try:
            channel = await bot.fetch_channel(channel_id)
            # after 파라미터 사용 (None이면 전체 조회)
            async for message in channel.history(limit=None, after=overall_latest_timestamp, oldest_first=True):
                if await process_heartbeat_message(message, channel_id_str, channel_name):
                    history_processed_count += 1 # 처리된 경우만 카운트
            print(f"    [{channel_name}] 스캔 완료.")
        except (discord.NotFound, discord.Forbidden, Exception) as e:
            print(f"❌ [{channel_name}] 채널 접근/조회 오류: {e}")

    print(f"✅ 채널 히스토리 스캔 완료 ({history_processed_count}개 처리됨). 메모리 최신 상태 로드됨.")
    print(f'👂 감시 채널: {list(TARGET_CHANNEL_IDS.values())}')

@bot.event
async def on_message(message):
    """메시지 수신 시 실시간 처리"""
    if message.author == bot.user: return # 봇 메시지 무시
    if message.channel.id in TARGET_CHANNEL_IDS: # 대상 채널만 처리
        channel_id_str = str(message.channel.id)
        channel_name = TARGET_CHANNEL_IDS[message.channel.id]
        await process_heartbeat_message(message, channel_id_str, channel_name)

async def check_heartbeat_status():
    """주기적으로 메모리 기반 Heartbeat 상태 확인"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(60) # 60초 간격

        now_utc = datetime.now(timezone.utc)
        offline_threshold = timedelta(minutes=10)

        print("\n--- Heartbeat 상태 확인 (메모리 최신 기록 기준) ---")
        channel_status = {str(cid): {"online": [], "offline": []} for cid in TARGET_CHANNEL_IDS.keys()}

        if not heartbeat_records:
             print("  표시할 Heartbeat 데이터가 없습니다.")
             continue

        for user_name, data in heartbeat_records.items():
            latest_record = data.get("latest_record")
            channel_id_str = data.get("channel_id_str")

            if not latest_record or not channel_id_str or channel_id_str not in channel_status:
                # print(f"⚠️ 사용자 '{user_name}' 메모리 데이터 오류/대상 채널 아님. 스킵됨.") # 로그 간소화
                continue

            user_status_name = user_name # 기본 이름
            is_online = False
            try:
                last_seen_iso = latest_record['timestamp']
                last_seen = datetime.fromisoformat(last_seen_iso.replace('Z', '+00:00'))
                if last_seen.tzinfo is None: last_seen = last_seen.replace(tzinfo=timezone.utc) # UTC 명시

                if now_utc - last_seen <= offline_threshold:
                    is_online = True
            except (KeyError, ValueError) as e:
                 print(f"⚠️ 사용자 '{user_name}' 시간 처리 오류 ({e}). Offline 처리.")
                 user_status_name = f"{user_name}(오류)" # 오류 시 이름에 표시

            if is_online:
                channel_status[channel_id_str]["online"].append(user_status_name)
            else:
                channel_status[channel_id_str]["offline"].append(user_status_name)

        # 결과 출력
        for channel_id_str, status in channel_status.items():
            try:
                channel_name = TARGET_CHANNEL_IDS.get(int(channel_id_str), f"Unknown ({channel_id_str})")
                print(f"[{channel_name}]")
                online_users = sorted(status["online"])
                offline_users = sorted(status["offline"])
                print(f"  Online ({len(online_users)}명): {', '.join(online_users) if online_users else '없음'}")
                if offline_users: print(f"  Offline ({len(offline_users)}명): {', '.join(offline_users)}")
            except ValueError: # int(channel_id_str) 실패 시
                print(f"- 잘못된 채널 ID 형식 무시: {channel_id_str}")

        print("----------------------------------------------\n")

async def main():
    """메인 실행 함수"""
    async with bot:
        bot.loop.create_task(check_heartbeat_status()) # 주기적 상태 확인 태스크 시작
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())