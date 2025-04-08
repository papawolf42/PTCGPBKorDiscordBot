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
        # last_seen_timestamp와 last_channel_id_str는 User 객체에서 더 이상 관리하지 않음

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

# --- 데이터 처리 함수 (Heartbeat) ---
def ensure_heartbeat_data_dir():
    """Heartbeat 데이터 저장 디렉토리 확인 및 생성"""
    if not os.path.exists(HEARTBEAT_DATA_DIR):
        try:
            os.makedirs(HEARTBEAT_DATA_DIR)
            print(f"📁 Heartbeat 데이터 디렉토리 생성: {HEARTBEAT_DATA_DIR}")
        except OSError as e:
            print(f"❌ Heartbeat 데이터 디렉토리 생성 실패: {e}")
            raise

def get_heartbeat_filepath(user_name):
    """사용자 Heartbeat JSON 파일 경로 반환"""
    return os.path.join(HEARTBEAT_DATA_DIR, f"{sanitize_filename(user_name)}.json")

def read_heartbeat_data(user_name):
    """사용자 Heartbeat JSON 파일 읽기 (없거나 오류 시 빈 리스트 반환)"""
    filepath = get_heartbeat_filepath(user_name)
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
            print(f"⚠️ 사용자 '{user_name}' Heartbeat 파일 형식이 리스트가 아님: {filepath}. 빈 리스트 반환.")
            return []
    except (json.JSONDecodeError, Exception) as e:
        print(f"❌ 사용자 '{user_name}' Heartbeat 파일 읽기/디코딩 오류: {e}. 빈 리스트 반환.")
        return []

def write_heartbeat_data(user_name, data_list):
    """사용자 Heartbeat 기록 리스트를 JSON 파일에 쓰기 (정렬 포함)"""
    filepath = get_heartbeat_filepath(user_name)
    try:
        data_list.sort(key=lambda x: x.get('timestamp', '')) # 쓰기 전 정렬 보장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ 사용자 '{user_name}' Heartbeat 파일 쓰기 오류: {e}")
        return False

def load_all_latest_heartbeat_data():
    """모든 사용자 Heartbeat 파일의 최신 기록을 메모리에 로드"""
    global heartbeat_records
    ensure_heartbeat_data_dir()
    print(f"💾 Heartbeat 데이터 폴더 스캔 및 최신 기록 로드 시작: {HEARTBEAT_DATA_DIR}")
    loaded_records = {}
    try:
        for filename in os.listdir(HEARTBEAT_DATA_DIR):
            if filename.endswith(".json"):
                user_name_from_file = filename[:-5] # .json 제거
                user_data = read_heartbeat_data(user_name_from_file) # 정렬된 리스트 반환
                if user_data:
                    latest_record = user_data[-1] # 마지막 항목이 최신
                    # channel_id_str 은 더 이상 사용/저장하지 않음
                    loaded_records[user_name_from_file] = {"latest_record": latest_record}
    except Exception as e:
        print(f"❌ 최신 Heartbeat 기록 로드 중 오류 발생: {e}")

    heartbeat_records = loaded_records
    print(f"✅ 최신 Heartbeat 기록 로드 완료: {len(heartbeat_records)}명")

# --- 데이터 처리 함수 (User Profile) ---
def ensure_user_data_dir():
    """사용자 프로필 데이터 저장 디렉토리 확인 및 생성"""
    if not os.path.exists(USER_DATA_DIR):
        try:
            os.makedirs(USER_DATA_DIR)
            print(f"📁 사용자 프로필 데이터 디렉토리 생성: {USER_DATA_DIR}")
        except OSError as e:
            print(f"❌ 사용자 프로필 데이터 디렉토리 생성 실패: {e}")
            raise

def get_user_profile_filepath(user_name):
    """사용자 프로필 JSON 파일 경로 반환"""
    return os.path.join(USER_DATA_DIR, f"{sanitize_filename(user_name)}.json")

def read_user_profile(user_name):
    """사용자 프로필 JSON 파일 읽기 (User 객체 반환, 없거나 오류 시 None)"""
    filepath = get_user_profile_filepath(user_name)
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        user = User.from_dict(data)
        if user:
            return user
        else:
            print(f"⚠️ 사용자 '{user_name}' 프로필 파일 데이터 유효하지 않음: {filepath}. None 반환.")
            return None
    except (json.JSONDecodeError, Exception) as e:
        print(f"❌ 사용자 '{user_name}' 프로필 파일 읽기/디코딩 오류: {e}. None 반환.")
        return None

def write_user_profile(user):
    """User 객체를 JSON 파일에 쓰기"""
    if not isinstance(user, User) or not user.name:
        print("❌ 잘못된 User 객체 전달됨. 쓰기 작업 건너뜀.")
        return False
    filepath = get_user_profile_filepath(user.name)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(user.to_dict(), f, indent=4, ensure_ascii=False)
        # print(f"💾 사용자 프로필 저장됨: {user.name}") # 로그 너무 많을 수 있어 주석 처리
        return True
    except Exception as e:
        print(f"❌ 사용자 '{user.name}' 프로필 파일 쓰기 오류: {e}")
        return False

def load_all_user_profiles():
    """모든 사용자 프로필 파일을 메모리에 로드"""
    global user_profiles
    ensure_user_data_dir()
    print(f"💾 사용자 프로필 로드 시작: {USER_DATA_DIR}")
    loaded_profiles = {}
    try:
        for filename in os.listdir(USER_DATA_DIR):
            if filename.endswith(".json"):
                user_name_from_file = filename[:-5] # .json 제거
                user = read_user_profile(user_name_from_file)
                if user:
                    loaded_profiles[user.name] = user # 파일 이름 대신 객체 내부 이름 사용
    except Exception as e:
        print(f"❌ 사용자 프로필 로드 중 오류 발생: {e}")

    user_profiles = loaded_profiles
    print(f"✅ 사용자 프로필 로드 완료: {len(user_profiles)}명")

# --- 사용자 정보 소스 처리 ---
async def update_user_profiles_from_source():
    """외부 소스(Pastebin)에서 사용자 정보를 가져와 프로필 업데이트"""
    print(f"🌐 사용자 정보 소스 업데이트 시작: {USER_INFO_SOURCE_URL}")
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
                if response.status == 200:
                    text_content = await response.text()
                else:
                    print(f"❌ 사용자 정보 소스({USER_INFO_SOURCE_URL}) 접근 실패: 상태 코드 {response.status}")
                    return

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
                                    # print(f"  🔄 사용자 정보 업데이트됨: {name} (ID: {discord_id}, Code: {code})")
                                    updated_count += 1
                                else:
                                    print(f"  ❌ 사용자 정보 저장 실패: {name}")
                        # else:
                            # print(f"  ❓ 소스에 있으나 프로필 없는 사용자: {name} (Heartbeat 기록이 먼저 필요할 수 있음)")
                            # 필요 시 여기서 새 User 생성 가능

                    # 다음 블록으로 이동 (보통 4-5줄 단위)
                    i += 3 # 기본적으로 3줄 이동 후 다음 루프에서 추가 검사
                    while i < len(lines) and not lines[i].strip().startswith("<@") and lines[i].strip() != "":
                        i += 1
                    continue # 다음 <@ 찾기
            i += 1 # <@ 시작 아니면 다음 줄로

        print(f"✅ 사용자 정보 소스 업데이트 완료: {updated_count}명 정보 업데이트됨.")

    except ImportError:
        print("❌ 'aiohttp' 라이브러리가 설치되지 않았습니다. Pastebin 데이터 로딩을 건너뜁니다.")
        print("   실행 환경에 `pip install aiohttp` 를 실행해주세요.")
    except aiohttp.ClientError as e:
        print(f"❌ 사용자 정보 소스({USER_INFO_SOURCE_URL}) 접근 중 네트워크 오류: {e}")
    except Exception as e:
        # import traceback
        # traceback.print_exc() # 상세 오류 확인용
        print(f"❌ 사용자 정보 소스 처리 중 예상치 못한 오류 발생: {e}")

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
            # print(f"⚠️ [{channel_name}] 사용자 이름 없는 메시지 건너뜀: {message.content[:50]}...")
            return False

        timestamp_dt = message.created_at.replace(tzinfo=timezone.utc)
        timestamp_iso = timestamp_dt.isoformat()

        # --- 1. Heartbeat 기록 처리 ---
        parsed_heartbeat_data = parse_heartbeat_message(message.content)
        # Heartbeat 기록에는 타임스탬프와 파싱된 데이터만 저장 (채널 ID 제외)
        heartbeat_record_specific = {
            "timestamp": timestamp_iso,
            **parsed_heartbeat_data
        }

        heartbeat_data_list = read_heartbeat_data(user_name)

        if any(record.get('timestamp') == timestamp_iso for record in heartbeat_data_list):
            return False

        heartbeat_data_list.append(heartbeat_record_specific)
        heartbeat_saved = False
        if write_heartbeat_data(user_name, heartbeat_data_list):
            # print(f"💾 Heartbeat 기록됨 [{channel_name}]: {user_name} ...") # 로그 간소화
            # 메모리(heartbeat_records) 업데이트 (채널 ID 없이)
            heartbeat_records[user_name] = {"latest_record": heartbeat_record_specific}
            heartbeat_saved = True
        # else: # 실패 로그는 write_heartbeat_data 에서 출력

        # --- 2. User 프로필 업데이트 ---
        user_profile = user_profiles.get(user_name)
        if not user_profile:
            user_profile = read_user_profile(user_name)
            if not user_profile:
                user_profile = User(user_name)
                print(f"✨ 신규 사용자 프로필 생성: {user_name}")

        # Heartbeat 데이터로 User 객체 업데이트 (이제 timestamp, channel_id는 없음)
        user_profile.update_from_heartbeat(parsed_heartbeat_data) # 파싱된 데이터만 전달

        # 업데이트된 User 객체를 메모리 및 파일에 저장
        user_profiles[user_name] = user_profile
        write_user_profile(user_profile) # 저장 실패 시 함수 내에서 로그 출력

        return heartbeat_saved

    except Exception as e:
        # import traceback
        # traceback.print_exc()
        print(f"❌ [{channel_name}] Heartbeat 처리 중 예외 발생: {e} | 사용자: {user_name} | 메시지: {message.content[:100]}...")
        return False

# --- 이벤트 핸들러 및 주기적 작업 ---
@bot.event
async def on_ready():
    """봇 준비 완료 시 실행"""
    print(f'✅ 로그인됨: {bot.user}')
    print("--- 초기화 시작 ---")
    # 데이터 디렉토리 확인 및 생성
    ensure_heartbeat_data_dir()
    ensure_user_data_dir()

    # 데이터 로딩
    print("💾 최신 Heartbeat 기록 로딩 시작...")
    load_all_latest_heartbeat_data()
    print("💾 사용자 프로필 로딩 시작...")
    load_all_user_profiles()

    # 사용자 정보 소스(Pastebin)에서 ID 및 Code 업데이트 시도
    await update_user_profiles_from_source()

    # 누락된 Heartbeat 기록 스캔
    overall_latest_timestamp = None
    if heartbeat_records:
        timestamps = []
        for data in heartbeat_records.values():
             record = data.get("latest_record")
             if record and 'timestamp' in record:
                 try:
                     # ISO 문자열 파싱 (UTC 가정)
                     ts_str = record['timestamp']
                     ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                     if ts.tzinfo is None: ts = ts.replace(tzinfo=timezone.utc)
                     timestamps.append(ts)
                 except ValueError:
                     # print(f"⚠️ 잘못된 타임스탬프 형식 발견 (로드 중): {record.get('timestamp')}")
                     pass # 오류 무시하고 계속 진행
        if timestamps:
            overall_latest_timestamp = max(timestamps)

    if overall_latest_timestamp:
        print(f"🔄 마지막 Heartbeat 기록 ({overall_latest_timestamp.isoformat()}) 이후 메시지 스캔")
    else:
        print("🔄 저장된 Heartbeat 기록 없음. 전체 채널 히스토리 스캔...")

    history_processed_count = 0
    total_scanned = 0
    scan_start_time = datetime.now()

    for channel_id, channel_name in TARGET_CHANNEL_IDS.items():
        channel_id_str = str(channel_id)
        scan_type = '누락분만' if overall_latest_timestamp else '전체'
        print(f"  [{channel_name}] 채널 기록 조회 중... ({scan_type})")
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
                if channel_scanned % 1000 == 0: # 로그 빈도 줄임
                     print(f"    [{channel_name}] {channel_scanned}개 메시지 스캔됨...")

            print(f"    [{channel_name}] 스캔 완료 ({channel_scanned}개 스캔, {channel_processed_count}개 신규 처리).")
        except (discord.NotFound, discord.Forbidden) as e:
            print(f"❌ [{channel_name}] 채널 접근 불가: {e}. 건너뜁니다.")
        except Exception as e:
            print(f"❌ [{channel_name}] 채널 기록 조회 중 오류: {e}")

    scan_end_time = datetime.now()
    scan_duration = scan_end_time - scan_start_time
    print(f"✅ 전체 채널 히스토리 스캔 완료 ({total_scanned}개 스캔, {history_processed_count}개 신규 Heartbeat 처리됨). 소요 시간: {scan_duration}")
    print(f'👂 감시 채널: {list(TARGET_CHANNEL_IDS.values())}')
    print("--- 초기화 완료 ---")

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

        print("\n--- 사용자 상태 확인 ---")
        online_users_status = []
        offline_users_status = []

        all_user_names = set(user_profiles.keys()) | set(heartbeat_records.keys())

        if not all_user_names:
             print("  표시할 사용자 데이터가 없습니다.")
             # await asyncio.sleep(60) # 루프 시작에서 이미 sleep 함
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
            barracks = user_profile.barracks if user_profile else 0

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
                    except ValueError:
                        last_seen_str = "시간오류"
                else:
                    last_seen_str = "시간없음"
            # else: Heartbeat 기록 자체가 없는 경우 (프로필만 있거나) -> Offline

            full_status_str = f"{status_prefix} {status_suffix}"
            if is_online:
                online_users_status.append(full_status_str)
            else:
                offline_users_status.append(f"{full_status_str} [마지막: {last_seen_str}]")

        # 결과 출력
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
    async with bot:
        bot.loop.create_task(check_heartbeat_status()) # 주기적 상태 확인 태스크 시작
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    # import traceback
    asyncio.run(main())