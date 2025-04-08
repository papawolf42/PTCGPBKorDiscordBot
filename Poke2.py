import discord
import asyncio
from datetime import datetime, timezone, timedelta
import json
import os
import re
import shutil
import logging # 로깅 모듈 추가
import random # Added import
import glob # glob 모듈 임포트 추가

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

# 테스트 플래그
test_flag = True # True로 설정 시 모든 등록 유저를 온라인으로 간주

# asyncio 이벤트 추가
initial_scan_complete_event = asyncio.Event()
# 파일 쓰기 동기화를 위한 락
friend_list_lock = asyncio.Lock()

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
    """사용자 Heartbeat 기록 리스트를 JSON 파일에 쓰기 (정렬 포함) 및 _last.json 업데이트"""
    filepath = get_data_filepath(user_name, HEARTBEAT_DATA_DIR)
    success = False
    try:
        data_list.sort(key=lambda x: x.get('timestamp', '')) # 쓰기 전 정렬 보장
        if write_json_file(filepath, data_list, "Heartbeat", user_name):
            success = True
            # --- _last.json 업데이트 로직 추가 ---
            if data_list: # 데이터가 있을 경우에만 최신 기록 저장
                latest_record = data_list[-1] # 정렬 후 마지막 요소가 최신
                last_filepath = filepath.replace(".json", "_last.json")
                last_data = {"latest_record": latest_record}
                if not write_json_file(last_filepath, last_data, "최신 Heartbeat", user_name):
                    logging.warning(f"⚠️ 사용자 '{user_name}'의 최신 Heartbeat 파일(_last.json) 쓰기 실패: {last_filepath}")
                    # _last.json 쓰기 실패는 전체 작업 실패로 간주하지 않음 (선택적)
            # --- _last.json 업데이트 로직 끝 ---
        return success # 기본 파일 쓰기 성공 여부 반환
    except Exception as e: # 정렬 중 오류 발생 가능성
        logging.error(f"❌ 사용자 '{user_name}' Heartbeat 데이터 처리(정렬/쓰기) 중 오류: {e}", exc_info=True)
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

    global heartbeat_records, user_profiles
    load_all_data(HEARTBEAT_DATA_DIR, "Heartbeat", read_heartbeat_data, heartbeat_records)
    load_all_data(USER_DATA_DIR, "사용자 프로필", read_user_profile, user_profiles)

    await update_user_profiles_from_source()

    # --- 누락된 Heartbeat 기록 스캔 최적화 ---
    logging.info("🔍 최신 Heartbeat 타임스탬프 찾는 중 (_last.json 파일 스캔)...")
    overall_latest_timestamp = None
    last_files = glob.glob(os.path.join(HEARTBEAT_DATA_DIR, "*_last.json"))
    logging.info(f"  발견된 _last.json 파일 수: {len(last_files)}")

    processed_files = 0
    for last_file in last_files:
        processed_files += 1
        if processed_files % 500 == 0: # 많은 파일 처리 시 로그 출력
             logging.info(f"  {processed_files}/{len(last_files)} 개의 _last.json 파일 처리 중...")
        try:
            with open(last_file, 'r', encoding='utf-8') as f:
                last_data = json.load(f)
                if "latest_record" in last_data and "timestamp" in last_data["latest_record"]:
                    ts_str = last_data["latest_record"]["timestamp"]
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                        if ts.tzinfo is None: ts = ts.replace(tzinfo=timezone.utc)

                        if overall_latest_timestamp is None or ts > overall_latest_timestamp:
                            overall_latest_timestamp = ts
                    except ValueError:
                        logging.warning(f"⚠️ 파일 '{os.path.basename(last_file)}'의 잘못된 타임스탬프 형식 발견: {ts_str}")
        except json.JSONDecodeError:
            logging.warning(f"⚠️ 파일 '{os.path.basename(last_file)}' 읽기/파싱 오류 (JSON 형식 오류)")
        except IOError as e:
            logging.warning(f"⚠️ 파일 '{os.path.basename(last_file)}' 읽기 오류: {e}")
        except Exception as e:
             logging.error(f"❌ _last.json 파일 처리 중 예상치 못한 오류 ({os.path.basename(last_file)}): {e}")


    if overall_latest_timestamp:
        logging.info(f"📊 전체 사용자 중 가장 최신 Heartbeat 타임스탬프: {overall_latest_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        logging.info("📊 기록된 최신 Heartbeat 타임스탬프를 찾지 못했습니다. (모든 메시지를 스캔할 수 있음)")
    # --- 누락된 Heartbeat 기록 스캔 최적화 끝 ---

    logging.info("📡 감시 채널 스캔 시작...")
    total_scanned = 0
    history_processed_count = 0

    # 채널별 스캔 시작 (overall_latest_timestamp 사용)
    for channel_id_str, channel_name in TARGET_CHANNEL_IDS.items():
        channel_id = int(channel_id_str)
        logging.info(f"  채널 스캔 중: {channel_name} ({channel_id})...")
        channel_processed_count = 0
        channel_scanned = 0
        try:
            channel = await bot.fetch_channel(channel_id)
            # overall_latest_timestamp가 있으면 그 이후만, 없으면 최근 10000개 (또는 전체)
            history_iterator = channel.history(limit=None, after=overall_latest_timestamp, oldest_first=True) if overall_latest_timestamp else channel.history(limit=10000, oldest_first=True)

            async for message in history_iterator:
                channel_scanned += 1
                total_scanned += 1
                if await process_heartbeat_message(message, channel_id_str, channel_name):
                    channel_processed_count += 1
                    history_processed_count += 1
                if channel_scanned % 2000 == 0:
                    logging.info(f"    [{channel_name}] {channel_scanned}개 메시지 스캔됨...")

            logging.info(f"    [{channel_name}] 스캔 완료 ({channel_scanned}개 스캔, {channel_processed_count}개 신규 처리).")

        except discord.NotFound:
            logging.error(f"❌ 채널을 찾을 수 없음: {channel_name} ({channel_id})")
        except discord.Forbidden:
            logging.error(f"❌ 채널 접근 권한 없음: {channel_name} ({channel_id})")
        except Exception as e:
            logging.error(f"❌ 채널 '{channel_name}' 스캔 중 오류 발생: {e}")
            import traceback
            traceback.print_exc() # 상세 오류 출력

    logging.info(f"📡 전체 채널 스캔 완료 (총 {total_scanned}개 스캔, {history_processed_count}개 신규 처리).")
    logging.info(f'👂 감시 채널: {list(TARGET_CHANNEL_IDS.values())}')
    logging.info("--- 초기화 완료 ---")

    initial_scan_complete_event.set()
    logging.info("🏁 초기 스캔 완료 이벤트 설정됨. 주기적 상태 확인 시작 가능.")

@bot.event
async def on_message(message):
    """메시지 수신 시 실시간 처리"""
    if message.author == bot.user: return # 봇 메시지 무시
    if message.channel.id in TARGET_CHANNEL_IDS: # 대상 채널만 처리
        channel_id_str = str(message.channel.id)
        channel_name = TARGET_CHANNEL_IDS[message.channel.id]
        await process_heartbeat_message(message, channel_id_str, channel_name)

# Placeholder for UserProfile and HeartbeatManager if they are not in the snippet
# Ensure these classes exist and have the methods used below (get_profile, save_profiles, get_last_heartbeat)
class UserProfile:
    profiles = {}
    data_file = 'data/user_data.json' # Example path

    @classmethod
    def load_profiles(cls):
        # Load profiles from data_file
        if os.path.exists(cls.data_file):
            try:
                with open(cls.data_file, 'r', encoding='utf-8') as f:
                    cls.profiles = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading user profiles: {e}")
                cls.profiles = {}
        else:
            cls.profiles = {}

    @classmethod
    def save_profiles(cls):
        # Save profiles to data_file
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(cls.data_file), exist_ok=True)
            with open(cls.data_file, 'w', encoding='utf-8') as f:
                json.dump(cls.profiles, f, indent=4)
        except IOError as e:
            print(f"Error saving user profiles: {e}")


    @classmethod
    def get_profile(cls, user_id_str):
        return cls.profiles.get(user_id_str)

class HeartbeatManager:
    heartbeats = {} # { user_id_str: last_heartbeat_datetime }
    # In a real scenario, this might load/save from a file or DB
    @classmethod
    def record_heartbeat(cls, user_id_str):
        cls.heartbeats[user_id_str] = datetime.now(timezone.utc)
        print(f"Heartbeat recorded for {user_id_str} at {cls.heartbeats[user_id_str]}")


    @classmethod
    def get_last_heartbeat(cls, user_id_str):
        return cls.heartbeats.get(user_id_str)


# --- Friend List Generation Logic ---
async def generate_friend_list_files(added_by_map, user_profiles_for_gen):
    """
    계산된 added_by_map을 기반으로 data/raw/ 디렉토리에
    {username}_added_by 와 {username} 파일을 생성합니다.
    !!! 이 함수는 호출 전에 friend_list_lock을 획득해야 합니다 !!!
    user_profiles_for_gen: { user_id_str: { 'username': ..., ... } }
    added_by_map: { u_id_str: [v1_id_str, v2_id_str...] }
    """
    # async with friend_list_lock: # 호출하는 쪽에서 락을 관리하도록 변경
    raw_dir = "data/raw"
    print(f"--- 친구 목록 파일 생성 시작 ({raw_dir}) ---")
    target_barracks = 170 # 목표 배럭 수 정의

    try:
        if os.path.exists(raw_dir):
            # print(f"기존 `{raw_dir}` 디렉토리 내용 삭제 중...") # 로그 간소화
            for filename in os.listdir(raw_dir):
                file_path = os.path.join(raw_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f'파일 삭제 실패 {file_path}. 이유: {e}')
        else:
            # print(f"`{raw_dir}` 디렉토리 생성 중...") # 로그 간소화
            os.makedirs(raw_dir, exist_ok=True)

        add_list = {user_id: [] for user_id in user_profiles_for_gen}

        for u_id_str, added_by_user_ids in added_by_map.items():
            u_profile_info = user_profiles_for_gen.get(u_id_str)
            if not u_profile_info:
                 # print(f"경고: ...") # 로그 간소화
                 continue

            display_name_u = u_profile_info.get('username', u_id_str)
            safe_display_name_u = sanitize_filename(display_name_u)
            added_by_path = os.path.join(raw_dir, f"{safe_display_name_u}_added_by")

            lines_for_added_by_file = []
            total_barracks_for_u = 0
            lines_for_added_by_file.append(f"Max Target Barracks: {target_barracks}")
            u_barracks = u_profile_info.get('barracks', '?')
            u_packs_list = u_profile_info.get('preferred_packs', [])
            u_packs_str = ",".join(u_packs_list) if u_packs_list else "?"
            lines_for_added_by_file.append(f"My Info: Username: {display_name_u} / Barracks: {u_barracks} / Packs: {u_packs_str}")
            lines_for_added_by_file.append("")
            lines_for_added_by_file.append("Friend Code\tUsername\tBarracks\tPacks")
            lines_for_added_by_file.append("-----------\t--------\t--------\t-----")

            for v_id_str in added_by_user_ids:
                v_profile_info = user_profiles_for_gen.get(v_id_str)
                if not v_profile_info:
                    # print(f"경고: ...") # 로그 간소화
                    continue

                v_friend_code = v_profile_info.get('friend_code', '코드없음')
                v_username = v_profile_info.get('username', v_id_str)
                v_barracks = v_profile_info.get('barracks', 0)
                v_packs_list = v_profile_info.get('preferred_packs', [])
                v_packs_str = ",".join(v_packs_list) if v_packs_list else "?"
                line = f"{v_friend_code}\t{v_username}\t{v_barracks}\t{v_packs_str}"
                lines_for_added_by_file.append(line)
                total_barracks_for_u += v_barracks

            lines_for_added_by_file.append("-----------\t--------\t--------\t-----")
            lines_for_added_by_file.append(f"Total Added Barracks:\t{total_barracks_for_u}")

            try:
                with open(added_by_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines_for_added_by_file))
            except IOError as e:
                 print(f"파일 쓰기 오류 ({added_by_path}): {e}")
                 continue

            u_friend_code = u_profile_info.get('friend_code')
            if not u_friend_code:
                continue

            for v_id_str in added_by_user_ids:
                if v_id_str in add_list:
                   add_list[v_id_str].append(u_friend_code)

        # print("`{username}` 파일 생성 중...") # 로그 간소화
        for v_id_str, friend_codes_to_add in add_list.items():
             v_profile_info = user_profiles_for_gen.get(v_id_str)
             if v_profile_info:
                 display_name_v = v_profile_info.get('username', v_id_str)
                 safe_display_name_v = sanitize_filename(display_name_v)
                 add_list_path = os.path.join(raw_dir, f"{safe_display_name_v}")
                 try:
                     with open(add_list_path, 'w', encoding='utf-8') as f:
                         f.write('\n'.join(friend_codes_to_add))
                 except IOError as e:
                    print(f"파일 쓰기 오류 ({add_list_path}): {e}")

        # print(f"--- 친구 목록 파일 생성 완료 ---") # finally 블록에서 출력

    except Exception as e:
        import traceback
        print(f"친구 목록 파일 생성 중 심각한 오류 발생: {e}")
        traceback.print_exc()
    # finally:
        # print(f"--- 친구 목록 파일 생성 완료 --- ") # 락 블록 밖에서 출력하는 것이 더 안전


async def update_friend_lists(online_users_profiles):
    """
    온라인 유저 목록을 기반으로 초기 친구 추가 목록({username}_added_by)을 계산합니다.
    online_users_profiles: { user_id_str: { 'username': str, 'barracks': int, 'preferred_packs': list, 'friend_code': str } }
    반환값: 계산된 added_by_map
    """
    print("--- 초기 친구 목록 계산 시작 ---")
    added_by_map = {} # 반환할 맵 초기화
    if not online_users_profiles:
        print("온라인 유저가 없어 초기 목록 계산을 건너뜁니다.")
        # 파일 정리는 generate 함수에서 처리
        return added_by_map # 빈 맵 반환

    online_user_ids = list(online_users_profiles.keys())
    total_barracks = sum(profile.get('barracks', 0) for profile in online_users_profiles.values())
    target_barracks = 170
    print(f"온라인 유저 수: {len(online_user_ids)}, 총 배럭: {total_barracks}, 목표 배럭: {target_barracks}")

    added_by_map = {user_id: [] for user_id in online_user_ids}
    add_count = {user_id: 0 for user_id in online_user_ids}

    if total_barracks < target_barracks:
        print("시나리오 1: 총 배럭 < 170. 모든 유저가 서로 추가합니다.")
        for u_id in online_user_ids:
            added_by_map[u_id] = [v_id for v_id in online_user_ids if u_id != v_id]
        # print(f"...")
    else:
        print("시나리오 2/3: 총 배럭 >= 170. 유저별 목록 계산 시작 (친구 추가 수 균형 고려)...")
        for u_id in online_user_ids:
            u_profile = online_users_profiles[u_id]
            u_preferred_packs = set(u_profile.get('preferred_packs', []))

            preferred_matches_ids = []
            other_matches_ids = []

            for v_id in online_user_ids:
                if u_id == v_id: continue
                v_profile = online_users_profiles[v_id]
                v_packs = set(v_profile.get('preferred_packs', []))
                if u_preferred_packs and not u_preferred_packs.isdisjoint(v_packs):
                    preferred_matches_ids.append(v_id)
                else:
                    other_matches_ids.append(v_id)

            preferred_barracks_sum = sum(online_users_profiles[v_id].get('barracks', 0) for v_id in preferred_matches_ids)

            current_added_by_ids = []
            current_barracks = 0

            if preferred_barracks_sum >= target_barracks:
                preferred_matches_ids.sort(key=lambda v_id: add_count[v_id])
                for v_id in preferred_matches_ids:
                    v_barracks = online_users_profiles[v_id].get('barracks', 0)
                    if current_barracks + v_barracks <= target_barracks:
                        current_added_by_ids.append(v_id)
                        current_barracks += v_barracks
                        add_count[v_id] += 1
                    if current_barracks >= target_barracks:
                        break
            else:
                for v_id in preferred_matches_ids:
                    current_added_by_ids.append(v_id)
                    current_barracks += online_users_profiles[v_id].get('barracks', 0)
                    add_count[v_id] += 1

                needed_barracks = target_barracks - current_barracks
                other_matches_ids.sort(key=lambda v_id: add_count[v_id])
                for v_id in other_matches_ids:
                    v_barracks = online_users_profiles[v_id].get('barracks', 0)
                    if current_barracks + v_barracks <= target_barracks:
                       current_added_by_ids.append(v_id)
                       current_barracks += v_barracks
                       add_count[v_id] += 1
                    if current_barracks >= target_barracks:
                        break
            added_by_map[u_id] = current_added_by_ids

    # 파일 생성은 별도 함수에서 하므로 여기서는 계산된 맵만 반환
    print("--- 초기 친구 목록 계산 완료 ---")
    return added_by_map

# --- 최적화 로직 (Placeholder) ---
def calculate_optimized_lists(current_added_by_map, online_users_profiles):
    """ (Placeholder) 현재 친구 목록을 개선하는 로직. 실제 구현 필요. """
    print("--- 친구 목록 최적화 계산 시작 (Placeholder) ---")
    # TODO: 여기에 실제 최적화 알고리즘 구현
    # 예: 가장 많은 친구를 추가해야 하는 유저(v_max)와 가장 적은 친구를 추가해야 하는 유저(v_min) 찾기
    #     v_max 가 추가하는 u 중 일부를 v_min 이 추가하도록 변경 시도 (선호도, 배럭 조건 만족 시)
    # 현재는 단순히 원본 맵을 그대로 반환 (변화 없음)
    optimized_map = current_added_by_map.copy() # 수정하려면 복사본 사용
    print("--- 친구 목록 최적화 계산 완료 (Placeholder) ---")
    return optimized_map

async def optimize_and_apply_lists(initial_added_by_map, online_profiles):
    """ 최적화 계산 및 결과 적용 (변경 시에만 파일 생성) """
    if not initial_added_by_map or not online_profiles:
         print("최적화 건너뜀 (입력 데이터 부족)")
         return

    print("--- 유휴 시간 최적화 시작 ---")
    # 최적화 계산 수행
    optimized_map = calculate_optimized_lists(initial_added_by_map, online_profiles)

    # 변경점 비교
    if optimized_map != initial_added_by_map:
        print("🔄 최적화 결과 변경점 발견! 새로운 친구 목록 적용 중...")
        async with friend_list_lock: # 파일 쓰기 전에 락 획득
             await generate_friend_list_files(optimized_map, online_profiles)
        print("✅ 최적화된 친구 목록 적용 완료.")
    else:
        print(" değişiklik 없음. 최적화 결과 적용 안 함.")
    print("--- 유휴 시간 최적화 완료 ---")

# --- End Friend List Generation Logic ---


# 첫 실행 플래그 (제거)
# initial_run_complete = False

# @tasks.loop(seconds=60) # tasks.loop 사용 시 아래 main의 bot.loop.create_task 불필요
async def check_heartbeat_status():
    """주기적으로 메모리 기반 사용자 상태 확인 및 친구 목록 업데이트"""
    await bot.wait_until_ready()
    logging.info("⏳ 주기적 상태 확인 시작 대기 중 (초기 스캔 완료 후 진행)...")
    await initial_scan_complete_event.wait() # 초기 스캔 완료까지 대기
    logging.info("▶️ 주기적 상태 확인 시작!")

    raw_dir = "data/raw"

    while not bot.is_closed():
        print("\n--- 사용자 상태 확인 시작 ---")
        if test_flag:
            print("⚠️ 테스트 모드 활성화: 모든 등록 유저를 온라인으로 간주합니다.")

        now_utc = datetime.now(timezone.utc)
        offline_threshold = timedelta(minutes=15)

        online_users_status = []
        offline_users_status = []
        current_online_profiles = {}

        all_user_names = list(user_profiles.keys())

        if not all_user_names:
             print("  등록된 사용자가 없습니다.")
        else:
             print(f"  {len(all_user_names)}명의 등록된 사용자 상태 확인 중...")

        for user_name in all_user_names:
            user_profile : User | None = user_profiles.get(user_name)

            if not user_profile or not isinstance(user_profile, User):
                print(f"  경고: 사용자 '{user_name}'의 프로필(User 객체)을 찾을 수 없거나 형식이 잘못되었습니다.")
                continue

            user_id_str = user_profile.discord_id
            display_name = user_profile.name
            code_str = user_profile.code if user_profile.code else "코드?"
            discord_mention = f"<@{user_id_str}>" if user_id_str else "ID?"
            status_prefix = f"{display_name} ({discord_mention}, {code_str})"
            pack_select_str = user_profile.pack_select
            if isinstance(pack_select_str, list):
                pack_select_str = ','.join(pack_select_str) if pack_select_str else "?"
            status_suffix = f"(v:{user_profile.version}|t:{user_profile.type}|p:{pack_select_str}|b:{user_profile.barracks})"
            full_status_str = f"{status_prefix} {status_suffix}"

            is_online = False
            last_heartbeat_dt = None # 오프라인 상태 문자열 출력을 위해 초기화

            if test_flag:
                is_online = True # 테스트 모드 시 무조건 온라인
            else:
                # 실제 하트비트 체크 로직
                latest_heartbeat_info = heartbeat_records.get(user_name)
                if latest_heartbeat_info and "latest_record" in latest_heartbeat_info:
                    latest_record = latest_heartbeat_info["latest_record"]
                    last_seen_iso = latest_record.get("timestamp")
                    if last_seen_iso:
                        try:
                            ts = datetime.fromisoformat(last_seen_iso.replace('Z', '+00:00'))
                            if ts.tzinfo is None: ts = ts.replace(tzinfo=timezone.utc)
                            last_heartbeat_dt = ts
                            if (now_utc - last_heartbeat_dt) <= offline_threshold:
                                is_online = True
                        except ValueError:
                             logging.warning(f"⚠️ 사용자 '{user_name}'의 잘못된 타임스탬프 형식 발견 (상태 확인 중): {last_seen_iso}")
                             # last_heartbeat_dt 는 None 유지

            if is_online:
                online_users_status.append(f"🟢 {full_status_str}")

                if user_id_str:
                    pref_packs = user_profile.pack_select
                    if isinstance(pref_packs, str):
                         pref_packs = [pref_packs] if pref_packs and pref_packs != "Unknown" else []

                    current_online_profiles[user_id_str] = {
                         'username': display_name,
                         'barracks': user_profile.barracks,
                         'preferred_packs': pref_packs,
                         'friend_code': user_profile.code
                     }
                else:
                     # 테스트 모드에서도 ID 없는 유저는 친구 목록 생성에서 제외
                     print(f"  경고: 온라인 사용자 '{display_name}'의 Discord ID가 없어 친구 목록 생성에서 제외됩니다.")
            else:
                # 테스트 모드가 아닐 때만 오프라인 처리
                last_seen_str = last_heartbeat_dt.strftime('%Y-%m-%d %H:%M:%S') if last_heartbeat_dt else "기록 없음"
                offline_users_status.append(f"🔴 {full_status_str} [마지막: {last_seen_str}]")

        print(f"--- 확인 시간: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} ---")
        print(f"--- Online ({len(current_online_profiles)}명) ---")
        for status in online_users_status: print(f"  {status}")
        print(f"--- Offline ({len(offline_users_status)}명) ---")
        for status in offline_users_status: print(f"  {status}")
        print("----------------------------------------------")

        # --- 친구 목록 업데이트 및 최적화 로직 호출 ---
        # 1. 기본 친구 목록 계산 (매번 실행)
        initial_map = await update_friend_lists(current_online_profiles)

        # 2. 계산된 목록으로 파일 쓰기 (락 사용)
        async with friend_list_lock:
             print("기본 친구 목록 파일 생성 시도...")
             await generate_friend_list_files(initial_map, current_online_profiles)
             print("기본 친구 목록 파일 생성 완료.")

        # 3. 유휴 시간 최적화 시도 (별도 함수 호출)
        # 이 함수는 내부적으로 변경이 있을 때만 락을 잡고 파일을 씀
        await optimize_and_apply_lists(initial_map, current_online_profiles)

        print("--- 사용자 상태 확인 및 목록 업데이트 완료 ---")
        await asyncio.sleep(60)


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