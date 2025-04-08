import discord
import asyncio
from datetime import datetime, timezone, timedelta
import json
import os
import re
import shutil
import logging # 로깅 모듈 추가

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# --- 상수 정의 ---
GROUP1_CHANNEL_ID = os.getenv('DISCORD_GROUP1_HEARTBEAT_ID')
GROUP3_CHANNEL_ID = os.getenv('DISCORD_GROUP3_HEARTBEAT_ID')
TARGET_CHANNEL_IDS = {GROUP1_CHANNEL_ID: "Group1", GROUP3_CHANNEL_ID: "Group3"}
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN') # 봇 토큰

HEARTBEAT_DATA_DIR = "data/heartbeat_data" # 데이터 저장 폴더
USER_DATA_DIR = "data/user_data" # 사용자 프로필 데이터 저장 폴더
USER_INFO_SOURCE_URL = "os.getenv('PASTEBIN_URL')" # 사용자 정보 소스 URL

# --- 봇 설정 ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True # 히스토리 조회에 필요할 수 있음
bot = discord.Client(intents=intents)

# --- 전역 변수 ---
# 사용자별 최신 heartbeat 기록 (메모리): {user_name: {"latest_record": dict}}
heartbeat_records = {}
# 사용자 프로필 정보 (메모리): {user_name: User}
user_profiles = {}

# --- User 클래스 정의 ---
class User:
    def __init__(self, name):
        self.name = name
        self.barracks = 0
        self.version = "Unknown"
        self.type = "Unknown"
        self.pack_select = "Unknown"
        self.code: str | None = None # 친구 코드
        self.discord_id: str | None = None # 디스코드 ID

    def update_from_heartbeat(self, heartbeat_data):
        """Heartbeat 데이터로 사용자 정보 업데이트 (타임스탬프/채널 제외)"""
        self.barracks = heartbeat_data.get('barracks', self.barracks)
        self.version = heartbeat_data.get('version', self.version)
        self.type = heartbeat_data.get('type', self.type)
        self.pack_select = heartbeat_data.get('select', self.pack_select)

    def update_identity(self, code: str | None, discord_id: str | None):
        """코드 및 디스코드 ID 업데이트"""
        if code:
            self.code = code
        if discord_id:
            self.discord_id = discord_id

    def to_dict(self):
        """User 객체를 딕셔너리로 변환"""
        return {
            'name': self.name,
            'barracks': self.barracks,
            'version': self.version,
            'type': self.type,
            'pack_select': self.pack_select,
            'code': self.code,
            'discord_id': self.discord_id,
        }

    @classmethod
    def from_dict(cls, data):
        """딕셔너리로부터 User 객체 생성"""
        if not data or 'name' not in data:
            return None
        user = cls(data['name'])
        user.barracks = data.get('barracks', 0)
        user.version = data.get('version', "Unknown")
        user.type = data.get('type', "Unknown")
        user.pack_select = data.get('pack_select', "Unknown")
        user.code = data.get('code') # 없으면 None
        user.discord_id = data.get('discord_id') # 없으면 None
        return user

# --- 데이터 처리 함수 (공통) ---
def sanitize_filename(name):
    """사용자 이름을 안전한 파일명으로 변환"""
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    return name[:100] # 100자 제한

def ensure_data_dir(dir_path, dir_type_name):
    """데이터 저장 디렉토리 확인 및 생성"""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            logging.info(f"📁 {dir_type_name} 데이터 디렉토리 생성: {dir_path}")
        except OSError as e:
            logging.error(f"❌ {dir_type_name} 데이터 디렉토리 생성 실패: {e}", exc_info=True)
            raise

def get_data_filepath(user_name, base_dir):
    """사용자 데이터 JSON 파일 경로 반환"""
    return os.path.join(base_dir, f"{sanitize_filename(user_name)}.json")

def read_json_file(filepath, data_type_name, user_name, default_value):
    """JSON 파일 읽기 (오류 시 기본값 반환)"""
    if not os.path.exists(filepath):
        return default_value
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.warning(f"⚠️ 사용자 '{user_name}' {data_type_name} 파일 JSON 디코딩 오류: {filepath}. 기본값 반환. Error: {e}")
        return default_value
    except OSError as e:
        logging.error(f"❌ 사용자 '{user_name}' {data_type_name} 파일 읽기 오류: {filepath}. Error: {e}", exc_info=True)
        return default_value

def write_json_file(filepath, data, data_type_name, user_name):
    """JSON 파일 쓰기"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except OSError as e:
        logging.error(f"❌ 사용자 '{user_name}' {data_type_name} 파일 쓰기 오류: {filepath}. Error: {e}", exc_info=True)
        return False

# --- 데이터 처리 함수 (Heartbeat) ---
def read_heartbeat_data(user_name):
    """사용자 Heartbeat JSON 파일 읽기 (없거나 오류 시 빈 리스트 반환)"""
    filepath = get_data_filepath(user_name, HEARTBEAT_DATA_DIR)
    data = read_json_file(filepath, "Heartbeat", user_name, [])
    if isinstance(data, list):
        valid_data = [r for r in data if isinstance(r, dict) and 'timestamp' in r]
        valid_data.sort(key=lambda x: x.get('timestamp', ''))
        return valid_data
    elif data: # 파일은 읽었으나 형식이 리스트가 아닐 때
        logging.warning(f"⚠️ 사용자 '{user_name}' Heartbeat 파일 형식이 리스트가 아님: {filepath}. 빈 리스트 반환.")
    return []

def write_heartbeat_data(user_name, data_list):
    """사용자 Heartbeat 기록 리스트를 JSON 파일에 쓰기 (정렬 포함)"""
    filepath = get_data_filepath(user_name, HEARTBEAT_DATA_DIR)
    try:
        data_list.sort(key=lambda x: x.get('timestamp', '')) # 쓰기 전 정렬 보장
        return write_json_file(filepath, data_list, "Heartbeat", user_name)
    except Exception as e: # 정렬 중 오류 발생 가능성 (매우 낮음)
        logging.error(f"❌ 사용자 '{user_name}' Heartbeat 데이터 정렬 중 오류: {e}", exc_info=True)
        return False

# --- 데이터 처리 함수 (User Profile) ---
def read_user_profile(user_name):
    """사용자 프로필 JSON 파일 읽기 (User 객체 반환, 없거나 오류 시 None)"""
    filepath = get_data_filepath(user_name, USER_DATA_DIR)
    data = read_json_file(filepath, "프로필", user_name, None)
    if data:
        user = User.from_dict(data)
        if user:
            return user
        else:
            logging.warning(f"⚠️ 사용자 '{user_name}' 프로필 파일 데이터 유효하지 않음: {filepath}. None 반환.")
    return None

def write_user_profile(user):
    """User 객체를 JSON 파일에 쓰기"""
    if not isinstance(user, User) or not user.name:
        logging.warning("❌ 잘못된 User 객체 전달됨. 쓰기 작업 건너뜀.")
        return False
    filepath = get_data_filepath(user.name, USER_DATA_DIR)
    return write_json_file(filepath, user.to_dict(), "프로필", user.name)

# --- 데이터 로딩 함수 (공통) ---
def load_all_data(data_dir, data_type_name, read_func, target_dict):
    """지정된 디렉토리에서 모든 데이터 파일을 로드하여 target_dict 업데이트"""
    ensure_data_dir(data_dir, data_type_name)
    logging.info(f"💾 {data_type_name} 데이터 폴더 스캔 및 로드 시작: {data_dir}")
    loaded_count = 0
    try:
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                user_name_from_file = filename[:-5]
                data = read_func(user_name_from_file) # 각 타입에 맞는 읽기 함수 사용
                if data:
                    if data_type_name == "Heartbeat":
                        if isinstance(data, list) and data: # read_heartbeat_data는 리스트 반환
                            target_dict[user_name_from_file] = {"latest_record": data[-1]}
                            loaded_count += 1
                    elif data_type_name == "사용자 프로필":
                        # read_user_profile은 User 객체 또는 None 반환
                        target_dict[data.name] = data # 파일 이름 대신 객체 이름 사용
                        loaded_count += 1

    except OSError as e:
        logging.error(f"❌ {data_type_name} 데이터 로드 중 디렉토리 오류 발생: {data_dir}. Error: {e}", exc_info=True)
    except Exception as e: # 예상치 못한 오류 (read_func 내부 오류 등)
        logging.error(f"❌ {data_type_name} 데이터 로드 중 예상치 못한 오류 발생: {e}", exc_info=True)

    logging.info(f"✅ {data_type_name} 데이터 로드 완료: {loaded_count}명")
    # return target_dict # 전역 변수를 직접 수정하므로 반환값 사용 안 함

# --- 사용자 정보 소스 처리 ---
async def update_user_profiles_from_source():
    """외부 소스(Pastebin)에서 사용자 정보를 가져와 프로필 업데이트"""
    logging.info(f"🌐 사용자 정보 소스 업데이트 시작: {USER_INFO_SOURCE_URL}")
    updated_count = 0
    try:
        # !!! 중요: 아래 코드는 aiohttp 라이브러리가 필요합니다.
        # 만약 환경에 없다면 `pip install aiohttp` 로 설치해야 합니다.
        # 또는 표준 라이브러리 urllib.request 등을 사용하여 동기적으로 처리하거나,
        # 별도의 스레드에서 실행해야 할 수 있습니다.
        # 여기서는 aiohttp 사용을 가정합니다.
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(USER_INFO_SOURCE_URL) as response:
                response.raise_for_status() # 오류 발생 시 예외 발생
                text_content = await response.text()

        lines = text_content.splitlines()
        i = 0
        while i < len(lines):
            line1 = lines[i].strip()
            if line1.startswith("<@") and line1.endswith(">"):
                discord_id_match = re.search(r"<@(\d+)>", line1)
                if discord_id_match and i + 2 < len(lines):
                    discord_id = discord_id_match.group(1)
                    code = lines[i+1].strip()
                    name_line = lines[i+2].strip()
                    # 이름 추출 (첫 단어 또는 공백 전까지)
                    name = name_line.split()[0] if name_line else None

                    if name and code and discord_id:
                        # 메모리에 있는 User 객체 찾기
                        user_profile = user_profiles.get(name)
                        if user_profile:
                            # 변경 사항 확인 후 업데이트 및 저장
                            if user_profile.discord_id != discord_id or user_profile.code != code:
                                user_profile.update_identity(code=code, discord_id=discord_id)
                                if write_user_profile(user_profile):
                                    # logging.debug(f"  🔄 사용자 정보 업데이트됨: {name} (ID: {discord_id}, Code: {code})")
                                    updated_count += 1
                                # else: 실패 시 write_user_profile에서 에러 로그 기록
                        # else:
                            # logging.debug(f"  ❓ 소스에 있으나 프로필 없는 사용자: {name} (Heartbeat 기록이 먼저 필요할 수 있음)")
                            # 필요 시 여기서 새 User 생성 가능

                    # 다음 블록으로 이동 (보통 4-5줄 단위)
                    i += 3 # 기본적으로 3줄 이동 후 다음 루프에서 추가 검사
                    while i < len(lines) and not lines[i].strip().startswith("<@") and lines[i].strip() != "":
                        i += 1
                    continue # 다음 <@ 찾기
            i += 1 # <@ 시작 아니면 다음 줄로

        logging.info(f"✅ 사용자 정보 소스 업데이트 완료: {updated_count}명 정보 업데이트됨.")

    except ImportError:
        logging.error("❌ 'aiohttp' 라이브러리가 설치되지 않았습니다. Pastebin 데이터 로딩을 건너뜁니다.")
        logging.error("   실행 환경에 `pip install aiohttp` 를 실행해주세요.")
    except aiohttp.ClientError as e:
        logging.error(f"❌ 사용자 정보 소스({USER_INFO_SOURCE_URL}) 접근 중 네트워크 오류: {e}")
    except Exception as e:
        logging.error(f"❌ 사용자 정보 소스 처리 중 예상치 못한 오류 발생: {e}", exc_info=True)

# --- Heartbeat 메시지 파싱 ---
def parse_heartbeat_message(content):
    """메시지 내용에서 heartbeat 정보 추출"""
    data = {'barracks': 0, 'version': 'Unknown', 'type': 'Unknown', 'select': 'Unknown'}
    online_line = next((line.strip() for line in content.splitlines() if line.strip().lower().startswith("online:")), None)
    if online_line:
        # "Online:" 다음의 숫자들을 찾음 (쉼표 포함 가능성 고려)
        numbers_str = online_line.split(":", 1)[1].strip()
        # 쉼표 제거 후 공백 기준으로 분리하여 숫자만 추출
        numbers_in_line = [num for num in re.findall(r'\b\d+\b', numbers_str)]
        data['barracks'] = len(numbers_in_line)

    version_match = re.search(r"^Version:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    if version_match: data['version'] = version_match.group(1).strip()
    type_match = re.search(r"^Type:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    if type_match: data['type'] = type_match.group(1).strip()
    select_match = re.search(r"^Select:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    if select_match: data['select'] = select_match.group(1).strip()
    return data

async def process_heartbeat_message(message, channel_id_str, channel_name):
    """Heartbeat 메시지 처리 (Heartbeat 기록 및 User 프로필 업데이트)"""
    if "Online:" not in message.content: return False

    user_name = "Unknown User"
    try:
        user_name = message.content.split("\n")[0].strip()
        if not user_name:
            # logging.debug(f"⚠️ [{channel_name}] 사용자 이름 없는 메시지 건너뜀: {message.content[:50]}...")
            return False

        timestamp_dt = message.created_at.replace(tzinfo=timezone.utc)
        timestamp_iso = timestamp_dt.isoformat()

        # --- 1. Heartbeat 기록 처리 ---
        parsed_heartbeat_data = parse_heartbeat_message(message.content)
        heartbeat_record_specific = {
            "timestamp": timestamp_iso,
            **parsed_heartbeat_data
        }

        heartbeat_data_list = read_heartbeat_data(user_name)

        if any(record.get('timestamp') == timestamp_iso for record in heartbeat_data_list):
            return False # 중복 처리 방지

        heartbeat_data_list.append(heartbeat_record_specific)
        heartbeat_saved = False
        if write_heartbeat_data(user_name, heartbeat_data_list):
            # logging.debug(f"💾 Heartbeat 기록됨 [{channel_name}]: {user_name} ...") # 너무 빈번할 수 있어 주석 처리 또는 DEBUG 레벨
            # 메모리(heartbeat_records) 업데이트
            heartbeat_records[user_name] = {"latest_record": heartbeat_record_specific}
            heartbeat_saved = True
        # else: 실패 로그는 write_heartbeat_data 에서 출력

        # --- 2. User 프로필 업데이트 ---
        user_profile = user_profiles.get(user_name)
        if not user_profile:
            user_profile = read_user_profile(user_name)
            if not user_profile:
                user_profile = User(user_name)
                logging.info(f"✨ 신규 사용자 프로필 생성: {user_name}")

        # Heartbeat 데이터로 User 객체 업데이트
        user_profile.update_from_heartbeat(parsed_heartbeat_data)

        # 업데이트된 User 객체를 메모리 및 파일에 저장
        user_profiles[user_name] = user_profile
        write_user_profile(user_profile) # 저장 실패 시 함수 내에서 로그 출력

        return heartbeat_saved # Heartbeat 저장 성공 여부 반환

    except Exception as e:
        logging.error(f"❌ [{channel_name}] Heartbeat 처리 중 예외 발생: {e} | 사용자: {user_name} | 메시지: {message.content[:100]}...", exc_info=True)
        return False

# --- 이벤트 핸들러 및 주기적 작업 ---
@bot.event
async def on_ready():
    """봇 준비 완료 시 실행"""
    logging.info(f'✅ 로그인됨: {bot.user}')
    logging.info("--- 초기화 시작 ---")

    # 데이터 디렉토리 확인/생성 (load_all_data 내부에서 호출됨)
    # ensure_data_dir(HEARTBEAT_DATA_DIR, "Heartbeat")
    # ensure_data_dir(USER_DATA_DIR, "사용자 프로필")

    # 데이터 로딩 (전역 변수 직접 업데이트)
    global heartbeat_records, user_profiles
    load_all_data(HEARTBEAT_DATA_DIR, "Heartbeat", read_heartbeat_data, heartbeat_records)
    load_all_data(USER_DATA_DIR, "사용자 프로필", read_user_profile, user_profiles)

    # 사용자 정보 소스(Pastebin)에서 ID 및 Code 업데이트 시도
    await update_user_profiles_from_source()

    # 누락된 Heartbeat 기록 스캔
    overall_latest_timestamp = None
    if heartbeat_records:
        timestamps = []
        for user_name, data in heartbeat_records.items():
            record = data.get("latest_record")
            if record and 'timestamp' in record:
                try:
                    ts_str = record['timestamp']
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    if ts.tzinfo is None: ts = ts.replace(tzinfo=timezone.utc)
                    timestamps.append(ts)
                except ValueError:
                    logging.warning(f"⚠️ 사용자 '{user_name}'의 잘못된 타임스탬프 형식 발견 (로드 중): {record.get('timestamp')}")
                    pass # 오류 무시하고 계속 진행
        if timestamps:
            overall_latest_timestamp = max(timestamps)

    if overall_latest_timestamp:
        logging.info(f"🔄 마지막 Heartbeat 기록 ({overall_latest_timestamp.isoformat()}) 이후 메시지 스캔")
    else:
        logging.info("🔄 저장된 Heartbeat 기록 없음. 전체 채널 히스토리 스캔...")

    history_processed_count = 0
    total_scanned = 0
    scan_start_time = datetime.now()

    for channel_id, channel_name in TARGET_CHANNEL_IDS.items():
        channel_id_str = str(channel_id)
        scan_type = '누락분만' if overall_latest_timestamp else '전체'
        logging.info(f"  [{channel_name}] 채널 기록 조회 중... ({scan_type})")
        channel_processed_count = 0
        channel_scanned = 0
        try:
            channel = await bot.fetch_channel(channel_id)
            async for message in channel.history(limit=None, after=overall_latest_timestamp, oldest_first=True):
                channel_scanned += 1
                total_scanned += 1
                if await process_heartbeat_message(message, channel_id_str, channel_name):
                    channel_processed_count += 1
                    history_processed_count += 1
                if channel_scanned % 2000 == 0: # 로그 빈도 더 줄임
                    logging.info(f"    [{channel_name}] {channel_scanned}개 메시지 스캔됨...")

            logging.info(f"    [{channel_name}] 스캔 완료 ({channel_scanned}개 스캔, {channel_processed_count}개 신규 처리).")
        except discord.NotFound:
            logging.error(f"❌ [{channel_name}] 채널({channel_id})을 찾을 수 없습니다. 건너뜁니다.")
        except discord.Forbidden:
            logging.error(f"❌ [{channel_name}] 채널({channel_id}) 접근 권한이 없습니다. 건너뜁니다.")
        except discord.HTTPException as e:
             logging.error(f"❌ [{channel_name}] 채널 기록 조회 중 Discord API 오류: {e}", exc_info=True)
        except Exception as e:
            logging.error(f"❌ [{channel_name}] 채널 기록 조회 중 예상치 못한 오류: {e}", exc_info=True)

    scan_end_time = datetime.now()
    scan_duration = scan_end_time - scan_start_time
    logging.info(f"✅ 전체 채널 히스토리 스캔 완료 ({total_scanned}개 스캔, {history_processed_count}개 신규 Heartbeat 처리됨). 소요 시간: {scan_duration}")
    logging.info(f'👂 감시 채널: {list(TARGET_CHANNEL_IDS.values())}')
    logging.info("--- 초기화 완료 ---")

@bot.event
async def on_message(message):
    """메시지 수신 시 실시간 처리"""
    if message.author == bot.user: return # 봇 메시지 무시
    if message.channel.id in TARGET_CHANNEL_IDS: # 대상 채널만 처리
        channel_id_str = str(message.channel.id)
        channel_name = TARGET_CHANNEL_IDS[message.channel.id]
        await process_heartbeat_message(message, channel_id_str, channel_name)

async def check_heartbeat_status():
    """주기적으로 메모리 기반 사용자 상태 확인 (User 프로필 및 Heartbeat 기록 활용)"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(60) # 60초 간격

        now_utc = datetime.now(timezone.utc)
        offline_threshold = timedelta(minutes=10)

        # 로깅보다는 print가 적합한 상태 표시
        print("\n--- 사용자 상태 확인 ---")
        online_users_status = []
        offline_users_status = []

        all_user_names = set(user_profiles.keys()) | set(heartbeat_records.keys())

        if not all_user_names:
             print("  표시할 사용자 데이터가 없습니다.")
             continue

        for user_name in sorted(list(all_user_names)): # 이름 순 정렬
            user_profile = user_profiles.get(user_name)
            latest_heartbeat_info = heartbeat_records.get(user_name)

            # 기본 정보 조합 (프로필 우선)
            name = user_name
            code = user_profile.code if user_profile else "코드?"
            discord_id_str = f"<@{user_profile.discord_id}>" if user_profile and user_profile.discord_id else "ID?"
            version = user_profile.version if user_profile else "버전?"
            type_ = user_profile.type if user_profile else "타입?"
            pack_select = user_profile.pack_select if user_profile else "팩?"
            barracks = user_profile.barracks if user_profile else 0 # 프로필 또는 heartbeat에서 가져올 수 있도록 개선 여지 있음

            status_prefix = f"{name} ({discord_id_str}, {code})"
            status_suffix = f"(v:{version}|t:{type_}|p:{pack_select}|b:{barracks})"

            is_online = False
            last_seen_str = "기록 없음"

            if latest_heartbeat_info and "latest_record" in latest_heartbeat_info:
                latest_record = latest_heartbeat_info["latest_record"]
                last_seen_iso = latest_record.get("timestamp")
                if last_seen_iso:
                    try:
                        last_seen = datetime.fromisoformat(last_seen_iso.replace('Z', '+00:00'))
                        if last_seen.tzinfo is None: last_seen = last_seen.replace(tzinfo=timezone.utc)
                        last_seen_str = last_seen.strftime('%y/%m/%d %H:%M:%S') # 형식 변경

                        if now_utc - last_seen <= offline_threshold:
                            is_online = True
                            # 최신 heartbeat 정보로 barracks 업데이트 (프로필보다 최신일 수 있음)
                            barracks = latest_record.get('barracks', barracks)
                            # 필요하다면 version, type, pack_select도 여기서 업데이트 가능
                            status_suffix = f"(v:{latest_record.get('version', version)}|t:{latest_record.get('type', type_)}|p:{latest_record.get('select', pack_select)}|b:{barracks})"

                    except ValueError:
                        last_seen_str = "시간오류"
                        logging.warning(f"사용자 '{user_name}'의 마지막 접속 시간 처리 오류: {last_seen_iso}")
                else:
                    last_seen_str = "시간없음"
            # else: Heartbeat 기록 자체가 없는 경우 (프로필만 있거나) -> Offline

            full_status_str = f"{status_prefix} {status_suffix}"
            if is_online:
                online_users_status.append(full_status_str)
            else:
                offline_users_status.append(f"{full_status_str} [마지막: {last_seen_str}]")

        # 결과 출력 (여전히 print 사용)
        print(f"--- 확인 시간: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} ---")
        print(f"--- Online ({len(online_users_status)}명) ---")
        if online_users_status:
            for status in online_users_status: print(f"  {status}")
        else:
            print("  없음")

        print(f"--- Offline ({len(offline_users_status)}명) ---")
        if offline_users_status:
            for status in offline_users_status: print(f"  {status}")
        else:
            print("  없음")
        print("----------------------------------------------\n")

async def main():
    """메인 실행 함수"""
    try:
        async with bot:
            bot.loop.create_task(check_heartbeat_status()) # 주기적 상태 확인 태스크 시작
            await bot.start(DISCORD_TOKEN)
    except Exception as e:
        logging.critical(f"봇 실행 중 치명적인 오류 발생: {e}", exc_info=True)
    finally:
        logging.info("봇 종료.")

if __name__ == "__main__":
    # import traceback # 필요 시 주석 해제
    asyncio.run(main())