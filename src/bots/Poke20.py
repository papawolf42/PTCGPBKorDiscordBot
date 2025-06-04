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
from typing import List, Optional # 타입 힌트용
from discord import app_commands # app_commands 임포트 추가
from discord.ext import commands # commands 임포트 추가
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# --- 상수 정의 ---
YOUR_TEST_SERVER_ID = int(os.getenv('DISCORD_SERVER_ID')) # 실제 테스트 서버 ID


# Heartbeat 관련 채널 (기존)
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN') # 봇 토큰

# DATA_PATH 환경변수 사용
DATA_PATH = os.getenv('DATA_PATH', 'data')
HEARTBEAT_DATA_DIR = os.path.join(DATA_PATH, "heartbeat_data20") # 데이터 저장 폴더
USER_DATA_DIR = os.path.join(DATA_PATH, "user_data") # 사용자 프로필 데이터 저장 폴더
USER_INFO_SOURCE_URL = os.getenv('PASTEBIN_URL') # 사용자 정보 소스 URL
TARGET_BARRACKS_DEFAULT = 170 # 기본 목표 배럭 정의

# 팩 선호도 기본 순서
DEFAULT_PACK_ORDER = ["Buzzwole", "Solgaleo", "Lunala", "Shining", "Arceus", "Palkia", "Dialga", "Mew", "Pikachu", "Charizard", "Mewtwo"]
# 유효한 팩 목록 (자동완성 및 검증용)
VALID_PACKS = DEFAULT_PACK_ORDER[:] # 기본 순서를 복사하여 사용, 필요시 확장

# 오류 감지 및 알림 채널 (기존 ERROR_DETECT_CHANNEL_ID)
GODPACK_WEBHOOK_CHANNEL_ID = os.getenv('DISCORD_GROUP8_DETECT_ID')
BARRACKS_REDUCTION_STEP = 5 # 한 번에 줄일 목표 배럭 수
MIN_TARGET_BARRACKS = 100 # 최소 목표 배럭 (더 이상 줄이지 않음)

# --- 그룹 설정 (newGroup.py 정보 기반) ---
GROUP_CONFIGS = [
    {
        "NAME": "Group8",
        "HEARTBEAT_ID": int(os.getenv('DISCORD_GROUP8_HEARTBEAT_ID')), # Heartbeat (예시, 실제 그룹 ID에 맞게 조정 필요)
        "DETECT_ID": int(os.getenv('DISCORD_GROUP8_DETECT_ID')),
        "POSTING_ID": int(os.getenv('DISCORD_GROUP8_POSTING_ID')),
        "COMMAND_ID": int(os.getenv('DISCORD_GROUP8_COMMAND_ID')),
        "MUSEUM_ID": int(os.getenv('DISCORD_GROUP8_MUSEUM_ID')),
        "TAGS": {
            "Yet": int(os.getenv('DISCORD_GROUP8_TAG_YET')),
            "Good": int(os.getenv('DISCORD_GROUP8_TAG_GOOD')),
            "Bad": int(os.getenv('DISCORD_GROUP8_TAG_BAD')),
            "1P": int(os.getenv('DISCORD_GROUP8_TAG_1P')),
            "2P": int(os.getenv('DISCORD_GROUP8_TAG_2P')),
            "3P": int(os.getenv('DISCORD_GROUP8_TAG_3P')),
            "4P": int(os.getenv('DISCORD_GROUP8_TAG_4P')),
            "5P": int(os.getenv('DISCORD_GROUP8_TAG_5P')),
            "Notice": int(os.getenv('DISCORD_GROUP8_TAG_NOTICE'))
        }
    }
]

# --- 봇 설정 --- (Client -> Bot 변경)
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents) # Client -> Bot 변경, command_prefix 추가
# tree = app_commands.CommandTree(bot) # 이 줄 제거

# --- 전역 변수 ---
# 사용자별 최신 heartbeat 기록 (메모리): {user_name: {"latest_record": dict}}
heartbeat_records = {}
# 사용자 프로필 정보 (메모리): {user_name: User}
user_profiles = {}

# 테스트 플래그
test_flag = False # True로 설정 시 모든 등록 유저를 온라인으로 간주, False로 설정 시 온라인 유저만 감지

# 디버그 플래그
debug_flag = False # True로 설정 시 디스코드 메시지 전송을 건너뜁니다.

# asyncio 이벤트 추가
initial_scan_complete_event = asyncio.Event() # 기존 이벤트 (초기 스캔 완료 알림용)
initialization_complete = asyncio.Event() # 백그라운드 전체 초기화 완료 알림용
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
        self.group_name: str | None = None # 사용자의 현재 소속 그룹 (최신 Heartbeat 기반)
        self.custom_target_barracks: int | None = None # 사용자 지정 목표 배럭
        self.preferred_pack_order: list[str] | None = None # 사용자 지정 팩 선호도 순서
        self.graduated_packs: list[str] = [] # 졸업팩 목록 추가 (기본값 빈 리스트)

    def update_from_heartbeat(self, heartbeat_data, source_group_name: str | None = None): # source_group_name 인자 추가
        """Heartbeat 데이터 및 소스 그룹 정보로 사용자 정보 업데이트"""
        self.barracks = heartbeat_data.get('barracks', self.barracks)
        self.version = heartbeat_data.get('version', self.version)
        self.type = heartbeat_data.get('type', self.type)
        self.pack_select = heartbeat_data.get('select', self.pack_select)
        if source_group_name:
             # "GroupX-Heartbeat" -> "GroupX" 또는 그대로 사용
             self.group_name = source_group_name.split('-')[0] if '-' in source_group_name else source_group_name

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
            'group_name': self.group_name,
            'custom_target_barracks': self.custom_target_barracks,
            'preferred_pack_order': self.preferred_pack_order,
            'graduated_packs': self.graduated_packs,
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
        user.code = data.get('code')
        user.discord_id = data.get('discord_id')
        user.group_name = data.get('group_name')
        # custom_target_barracks 로드 시 정수형 변환 시도
        custom_target = data.get('custom_target_barracks')
        if custom_target is not None:
            try:
                user.custom_target_barracks = int(custom_target)
            except (ValueError, TypeError):
                logging.warning(f"⚠️ 사용자 '{user.name}'의 custom_target_barracks 값('{custom_target}')이 유효한 숫자가 아니므로 무시합니다.")
                user.custom_target_barracks = None # 유효하지 않으면 None으로 설정
        else:
            user.custom_target_barracks = None

        # preferred_pack_order 로드 (리스트 형태가 아니거나 없으면 None)
        preferred_order = data.get('preferred_pack_order')
        if isinstance(preferred_order, list):
            user.preferred_pack_order = preferred_order
        else:
            user.preferred_pack_order = None # 기본값은 None, read_user_profile에서 처리

        # graduated_packs 로드 (리스트 형태가 아니거나 없으면 빈 리스트)
        graduated = data.get('graduated_packs')
        if isinstance(graduated, list):
            user.graduated_packs = graduated
        else:
            user.graduated_packs = [] # 기본값 빈 리스트

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
    """사용자 프로필 JSON 파일 읽기 (User 객체 반환, 없거나 오류 시 None)
    파일 로드 시 필요한 키(custom_target_barracks, preferred_pack_order, graduated_packs)가 없으면 기본값을 추가하고 파일을 업데이트합니다.
    """
    filepath = get_data_filepath(user_name, USER_DATA_DIR)
    data = read_json_file(filepath, "프로필", user_name, None)
    if data:
        needs_update = False
        # --- custom_target_barracks 키 확인 및 기본값 추가 ---
        if 'custom_target_barracks' not in data:
            data['custom_target_barracks'] = TARGET_BARRACKS_DEFAULT # 기본값 추가
            needs_update = True
        # --- 키 확인 및 기본값 추가 끝 ---

        # --- preferred_pack_order 키 확인 및 기본값 생성/추가 ---
        # 조건: 키가 없거나, 값이 None이거나, 리스트 타입이 아닐 경우
        if 'preferred_pack_order' not in data or data.get('preferred_pack_order') is None or not isinstance(data.get('preferred_pack_order'), list):
            logging.info(f"  정보: 사용자 '{user_name}' 프로필에 preferred_pack_order 없거나 유효하지 않음. pack_select 기반으로 생성.")

            # 1. 사용자의 현재 pack_select 문자열 가져오기 및 파싱
            pack_select_str = data.get('pack_select', 'Unknown')
            selected_packs_from_str_raw = [p.strip() for p in pack_select_str.split(',') if p.strip()]

            # 유효한 팩 이름만 필터링하고 순서 유지 (중복 제거)
            selected_packs_ordered = []
            valid_pack_names_lower = {vp.lower(): vp for vp in VALID_PACKS}
            seen_packs = set()
            for raw_pack in selected_packs_from_str_raw:
                lower_pack = raw_pack.lower()
                if lower_pack in valid_pack_names_lower:
                    valid_pack_name = valid_pack_names_lower[lower_pack]
                    if valid_pack_name not in seen_packs:
                        selected_packs_ordered.append(valid_pack_name)
                        seen_packs.add(valid_pack_name)

            # 2. 새로운 preferred_pack_order 생성 시작
            new_order = selected_packs_ordered[:]
            current_packs_set = set(new_order) # 빠른 확인용

            # 3. 나머지 유효한 팩들 추가 (DEFAULT_PACK_ORDER 순서대로)
            for default_pack in DEFAULT_PACK_ORDER:
                if default_pack not in current_packs_set:
                    new_order.append(default_pack)

            data['preferred_pack_order'] = new_order
            needs_update = True
            logging.info(f"    -> 생성된 순서: {new_order}")
        # --- 키 확인 및 기본값 추가 끝 ---

        # --- graduated_packs 키 확인 및 기본값 추가 ---
        if 'graduated_packs' not in data or not isinstance(data.get('graduated_packs'), list):
            data['graduated_packs'] = [] # 기본값 빈 리스트 추가
            needs_update = True
        # --- 키 확인 및 기본값 추가 끝 ---

        user = User.from_dict(data)
        if user:
            # --- 파일 업데이트 (필요한 경우) ---
            if needs_update:
                logging.info(f"  💾 사용자 '{user_name}' 프로필 파일 업데이트 (필요한 기본값 추가/수정됨).")
                if not write_user_profile(user):
                    logging.warning(f"⚠️ 사용자 '{user_name}' 프로필 파일 업데이트 실패: {filepath}")
            # --- 파일 업데이트 끝 ---
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

    # --- Select/Opening 파싱 로직 수정 ---
    select_match = re.search(r"^Select:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    opening_match = re.search(r"^Opening:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)

    select_value = select_match.group(1).strip() if select_match else None
    opening_value = opening_match.group(1).strip() if opening_match else None

    if select_value and opening_value:
        # 둘 다 있으면 더 긴 값을 선택
        data['select'] = opening_value if len(opening_value) >= len(select_value) else select_value
        logging.debug(f"Heartbeat 파싱: Select와 Opening 모두 발견. 더 긴 값 선택: '{data['select']}'")
    elif opening_value:
        # Opening만 있으면 Opening 값 사용
        data['select'] = opening_value
    elif select_value:
        # Select만 있으면 Select 값 사용
        data['select'] = select_value
    # 둘 다 없으면 기본값 'Unknown' 유지
    # --- 파싱 로직 수정 끝 ---

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
        # 그룹 이름 추출 ("Group8-Heartbeat" -> "Group8" 또는 채널 이름 그대로)
        simple_group_name = channel_name.split('-')[0] if '-' in channel_name else channel_name

        heartbeat_record_specific = {
            "timestamp": timestamp_iso,
            "source_group": simple_group_name, # 소스 그룹 정보 추가
            **parsed_heartbeat_data
        }

        heartbeat_data_list = read_heartbeat_data(user_name)

        if any(record.get('timestamp') == timestamp_iso for record in heartbeat_data_list):
            return False

        heartbeat_data_list.append(heartbeat_record_specific)
        heartbeat_saved = False
        if write_heartbeat_data(user_name, heartbeat_data_list):
            # 메모리(heartbeat_records) 업데이트 시에도 source_group 포함
            heartbeat_records[user_name] = {
                "latest_record": heartbeat_record_specific,
                 # "source_group": simple_group_name # 최신 그룹 정보 저장 (check_heartbeat_status에서 사용) - heartbeat_records 로딩 시 처리되므로 중복 저장 불필요
            }
            heartbeat_saved = True

        # --- 2. User 프로필 업데이트 ---
        user_profile = user_profiles.get(user_name)
        if not user_profile:
            user_profile = read_user_profile(user_name)
            if not user_profile:
                user_profile = User(user_name)
                logging.info(f"✨ 신규 사용자 프로필 생성: {user_name}")

        # Heartbeat 데이터와 그룹 정보로 User 객체 업데이트
        user_profile.update_from_heartbeat(parsed_heartbeat_data, simple_group_name) # simple_group_name 전달

        user_profiles[user_name] = user_profile
        write_user_profile(user_profile)

        return heartbeat_saved

    except Exception as e:
        logging.error(f"❌ [{channel_name}] Heartbeat 처리 중 예외 발생: {e} | 사용자: {user_name} | 메시지: {message.content[:100]}...", exc_info=True)
        return False

# --- 이벤트 핸들러 및 주기적 작업 ---

async def perform_initial_setup():
    """시간이 오래 걸리는 초기화 작업을 수행하는 함수 (백그라운드 실행)"""
    logging.info("--- 초기화 시작 (백그라운드) ---")
    global heartbeat_records, user_profiles
    # 1. 데이터 로딩
    load_all_data(HEARTBEAT_DATA_DIR, "Heartbeat", read_heartbeat_data, heartbeat_records)
    load_all_data(USER_DATA_DIR, "사용자 프로필", read_user_profile, user_profiles)

    # 2. 최신 타임스탬프 스캔 (여전히 시간이 걸릴 수 있으므로 주의)
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

    # 3. 채널 히스토리 스캔 (가장 시간이 많이 걸리는 부분, 최적화 필요)
    logging.info("📡 감시 채널 스캔 시작 (백그라운드)...")
    total_scanned = 0
    history_processed_count = 0

    # 채널별 스캔 시작 (overall_latest_timestamp 사용)
    for config in GROUP_CONFIGS:
        group_name = config.get("NAME", "Unnamed Group")
        channel_id = config.get("HEARTBEAT_ID")
        if channel_id:
            logging.info(f"  채널 스캔 중: {group_name} ({channel_id})...")
            channel_processed_count = 0
            channel_scanned = 0
            try:
                # fetch_channel 대신 get_channel 사용 (캐시된 정보 우선 사용)
                channel = bot.get_channel(channel_id)
                if not channel:
                    # 캐시에 없으면 fetch_channel로 시도
                    try:
                        channel = await bot.fetch_channel(channel_id)
                    except discord.Forbidden:
                        logging.error(f"❌ 채널 접근 권한 없음: {group_name} ({channel_id})")
                        continue
                    except discord.NotFound:
                        logging.error(f"❌ 채널을 찾을 수 없음: {group_name} ({channel_id})")
                        continue
                
                # 채널 권한 검증
                guild = channel.guild if hasattr(channel, 'guild') else None
                if guild:
                    bot_member = guild.get_member(bot.user.id)
                    if bot_member:
                        permissions = channel.permissions_for(bot_member)
                        if not permissions.read_message_history:
                            logging.error(f"❌ 채널 메시지 기록 읽기 권한 없음: {group_name} ({channel_id})")
                            continue
                
                # overall_latest_timestamp가 있으면 그 이후만, 없으면 최근 10000개 (또는 전체)
                scan_after_timestamp = overall_latest_timestamp
                # 만약 저장된 최신 타임스탬프가 없거나, 너무 오래된 경우 (예: 1시간 이전)에는 최근 1시간만 조회
                if scan_after_timestamp is None or (datetime.now(timezone.utc) - scan_after_timestamp) > timedelta(hours=1):
                    scan_after_timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
                    logging.info(f"    최신 타임스탬프가 없거나 1시간 이상 경과되어, 최근 1시간({scan_after_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')})부터 스캔합니다.")

                # !!! 중요: limit=None은 매우 많은 메시지를 가져올 수 있어 시간이 오래 걸리고 API 제한에 걸릴 수 있습니다. !!!
                # 실제 운영 시에는 limit을 설정하거나 (예: limit=5000)
                # 또는 더 짧은 시간 범위(예: timedelta(minutes=30))로 제한하는 것이 좋습니다.
                history_iterator = channel.history(limit=None, after=scan_after_timestamp, oldest_first=True)

                async for message in history_iterator:
                    channel_scanned += 1
                    total_scanned += 1
                    if await process_heartbeat_message(message, str(channel_id), group_name):
                        channel_processed_count += 1
                        history_processed_count += 1
                    if channel_scanned % 2000 == 0:
                        logging.info(f"    [{group_name}] {channel_scanned}개 메시지 스캔됨...")

                logging.info(f"    [{group_name}] 스캔 완료 ({channel_scanned}개 스캔, {channel_processed_count}개 신규 처리).")
                initial_scan_complete_event.set() # 스캔 완료 이벤트는 여기서 설정 (기존 위치)

            except Exception as e:
                logging.error(f"❌ 채널 '{group_name}' 스캔 중 예상치 못한 오류 발생: {e}")
                import traceback
                traceback.print_exc() # 상세 오류 출력

    logging.info(f"📡 전체 채널 스캔 완료 (총 {total_scanned}개 스캔, {history_processed_count}개 신규 처리).")

    # 4. Pastebin 업데이트
    logging.info("🔄 Pastebin에서 사용자 정보를 가져오는 중 (백그라운드)...")
    await update_user_profiles_from_source()
    logging.info("✅ Pastebin 사용자 정보 업데이트 완료.")

    # 감시 채널 로깅 업데이트 (Heartbeat 및 Detect 채널 포함)
    monitored_channels = []
    for config in GROUP_CONFIGS:
        group_name = config.get("NAME", "Unnamed Group")
        if config.get("HEARTBEAT_ID"):
            monitored_channels.append(f"{group_name}-Heartbeat ({config['HEARTBEAT_ID']})")
        if config.get("DETECT_ID"):
            monitored_channels.append(f"{group_name}-Detect ({config['DETECT_ID']})")
    logging.info(f'👂 감시 채널: {", ".join(monitored_channels)}')

    logging.info("--- 초기화 완료 (백그라운드) ---")
    initialization_complete.set() # 모든 백그라운드 초기화 완료 시그널 설정


@bot.event
async def on_ready():
    """봇 준비 완료 시 실행 (최소화된 버전)"""
    logging.info(f'✅ 로그인됨: {bot.user}')

    # --- 명령어 트리 동기화 --- (필수 작업)
    test_guild = discord.Object(id=YOUR_TEST_SERVER_ID)
    try:
        # sync를 먼저 호출!
        await bot.tree.sync(guild=test_guild)
        logging.info(f"🌳 테스트 서버({YOUR_TEST_SERVER_ID})에 슬래시 명령어 동기화 완료.")
        # 전역 동기화 필요 시 주석 해제
        # synced_global = await bot.tree.sync()
        # logging.info(f"🌳 전역 슬래시 명령어 {len(synced_global)}개 동기화 시도 완료.")
    except Exception as e:
        logging.error(f"❌ 슬래시 명령어 동기화 실패: {e}", exc_info=True)

    logging.info("🚀 봇 준비 완료. 백그라운드 초기화 시작...")

    # 시간 오래 걸리는 작업은 백그라운드 태스크로 실행
    bot.loop.create_task(perform_initial_setup())

    logging.info(f'👂 오류 감지 및 알림 채널: {GODPACK_WEBHOOK_CHANNEL_ID}')


@bot.event
async def on_message(message):
    """메시지 수신 시 실시간 처리"""
    if message.author == bot.user: return # 봇 메시지 무시

    # --- 스레드 댓글 감지 및 목표 배럭 초기화 로직 ---
    if isinstance(message.channel, discord.Thread):
        # 이 스레드가 어떤 그룹의 포스팅 채널에 속하는지 확인
        thread_parent_id = message.channel.parent_id
        target_group_config = None
        for config in GROUP_CONFIGS:
            if config.get("POSTING_ID") == thread_parent_id:
                target_group_config = config
                break

        if target_group_config:
            logging.info(f"[{target_group_config['NAME']}-Posting] 스레드 댓글 감지 (작성자: {message.author.name}, ID: {message.author.id})")
            author_id_str = str(message.author.id)
            target_user_profile: User | None = None
            target_user_name = "Unknown"

            # 메모리에서 사용자 찾기
            for user_name, profile in user_profiles.items():
                if profile.discord_id == author_id_str:
                    target_user_profile = profile
                    target_user_name = user_name
                    break

            if target_user_profile:
                current_custom_target = target_user_profile.custom_target_barracks
                reset_value = 170 # 복구할 목표 배럭 값

                # 현재 설정값이 있고, 170 미만인 경우에만 복구 실행
                if current_custom_target is not None and current_custom_target < reset_value:
                    original_value_for_log = current_custom_target # Store original value for logging/message
                    logging.info(f"  - 사용자 '{target_user_name}'의 목표 배럭 복구 시도 (현재값: {original_value_for_log} -> {reset_value})")
                    target_user_profile.custom_target_barracks = reset_value
                    if write_user_profile(target_user_profile):
                        logging.info(f"  - 사용자 '{target_user_name}' 프로필 업데이트 성공 (목표 배럭 {reset_value}(으)로 복구됨).")
                        try:
                            if not debug_flag:
                                # ephemeral=True 를 사용하여 본인에게만 보이도록 알림 전송 (실제로 변경된 경우에만)
                                # await message.reply(f"✅ {message.author.mention}, 이 스레드에 댓글을 작성하여 목표 배럭이 `{original_value_for_log}`에서 `{reset_value}`(으)로 복구되었습니다.", ephemeral=True, delete_after=60) # 60초 후 자동 삭제
                                logging.info(f"  - 목표 배럭 복구 알림 메시지 전송 완료 (대상: {message.author.name}).")
                            else:
                                logging.info(f"  - [Debug Mode] 목표 배럭 복구 알림 메시지 전송 건너뜀.")
                        except discord.Forbidden:
                            logging.error(f"❌ 스레드 댓글 알림 메시지 전송 권한이 없습니다 (채널: {message.channel.id}).")
                        except Exception as e:
                            logging.error(f"❌ 스레드 댓글 알림 메시지 전송 중 오류 발생: {e}", exc_info=True)
                    else:
                        # 복구 실패 시 값 롤백
                        target_user_profile.custom_target_barracks = original_value_for_log
                        logging.error(f"  - 사용자 '{target_user_name}' 프로필 업데이트 실패 (목표 배럭 복구 실패).")
                        # 실패 시 알림 (선택 사항)
                        # await message.reply(f"❌ {message.author.mention}, 목표 배럭 복구 중 오류 발생.", ephemeral=True, delete_after=10)
                # else: # 복구 조건에 맞지 않으면 로그만 남기거나 아무것도 안 함
                    # if current_custom_target is None:
                    #     logging.info(f"  - 사용자 '{target_user_name}'의 목표 배럭이 설정되지 않아 복구 대상 아님.")
                    # elif current_custom_target >= reset_value:
                    #     logging.info(f"  - 사용자 '{target_user_name}'의 목표 배럭({current_custom_target})이 {reset_value} 이상이므로 복구 대상 아님.")

            else:
                logging.warning(f"  - 스레드 댓글 작성자(ID: {author_id_str})의 프로필 정보를 찾을 수 없습니다.")

            return # 스레드 댓글 처리가 완료되었으므로 함수 종료 (다른 on_message 로직 방지)
    # --- 스레드 댓글 감지 로직 끝 ---

    channel_id = message.channel.id
    content = message.content

    # --- 목표 배럭 자동 감소 로직 ---
    if channel_id == GODPACK_WEBHOOK_CHANNEL_ID and "Instance Main has been stuck" in content:
        logging.info(f"[{GODPACK_WEBHOOK_CHANNEL_ID}] 목표 배럭 초과 오류 감지됨.")
        discord_id_match = re.search(r"<@(\d+)>", content)
        if discord_id_match:
            discord_id_str = discord_id_match.group(1)
            logging.info(f"  - 대상 Discord ID 추출: {discord_id_str}")

            target_user_profile: User | None = None
            target_user_name = "Unknown User"

            for user_name, profile in user_profiles.items():
                if profile.discord_id == discord_id_str:
                    target_user_profile = profile
                    target_user_name = user_name
                    break

            if target_user_profile:
                logging.info(f"  - 사용자 프로필 찾음: {target_user_name}")
                current_target = target_user_profile.custom_target_barracks
                effective_current_target = current_target if current_target is not None else TARGET_BARRACKS_DEFAULT
                new_target_barracks = max(MIN_TARGET_BARRACKS, effective_current_target - BARRACKS_REDUCTION_STEP)

                if new_target_barracks < effective_current_target:
                    logging.info(f"  - 목표 배럭 변경 시도: {effective_current_target} -> {new_target_barracks}")
                    target_user_profile.custom_target_barracks = new_target_barracks

                    if write_user_profile(target_user_profile):
                        logging.info(f"  - 사용자 '{target_user_name}' 프로필 업데이트 성공.")
                        # 알림 메시지 전송 (test_flag 확인)
                        if not test_flag:
                            try:
                                if not debug_flag:
                                    alert_channel = message.channel
                                    alert_message = f"⚠️ 사용자 **{target_user_name}**(<@{discord_id_str}>) 목표 배럭 자동 조정: `{effective_current_target}` -> `{new_target_barracks}` (/목표배럭설정 명령어로 재설정가능)"
                                    await alert_channel.send(alert_message)
                                    logging.info(f"  - 알림 메시지 전송 완료 (채널: {alert_channel.id}).")
                                else:
                                    logging.info(f"  - [Debug Mode] 목표 배럭 자동 조정 알림 메시지 전송 건너뜀.")
                            except discord.Forbidden:
                                logging.error(f"❌ 알림 채널({message.channel.id})에 메시지를 보낼 권한이 없습니다.") # alert_channel 변수가 선언되지 않았을 수 있음
                            except Exception as e:
                                logging.error(f"❌ 알림 채널 메시지 전송 중 오류 발생: {e}", exc_info=True)
                        else:
                            logging.info(f"  - [Test Mode] 목표 배럭 조정 알림 메시지 전송 건너뜀.")
                    else:
                        logging.error(f"  - 사용자 '{target_user_name}' 프로필 업데이트 실패.")
                else:
                    logging.info(f"  - 목표 배럭이 이미 최소값({MIN_TARGET_BARRACKS}) 이하이거나 같으므로 변경하지 않음 (현재: {effective_current_target}).")
            else:
                logging.warning(f"  - Discord ID '{discord_id_str}'에 해당하는 사용자를 찾을 수 없습니다.")
            return
        else:
            logging.warning(f"  - 오류 메시지에서 Discord ID를 추출하지 못했습니다.")
            return

    # --- 기존 채널 확인 로직 ---
    # 모든 그룹 설정을 순회하며 해당 채널이 어떤 그룹의 어떤 채널인지 확인
    for config in GROUP_CONFIGS:
        group_name = config.get("NAME", "Unnamed Group")
        # Heartbeat 채널 확인 (기존 로직과 유사)
        heartbeat_channel_id = config.get("HEARTBEAT_ID")
        if heartbeat_channel_id and channel_id == heartbeat_channel_id:
            channel_id_str = str(channel_id)
            channel_name_for_log = f"{group_name}-Heartbeat" # 로그용 채널 이름
            # logging.info(f"Processing Heartbeat for {group_name}...") # 디버깅 로그 필요 시
            await process_heartbeat_message(message, channel_id_str, channel_name_for_log)
            return # 메시지 처리가 완료되었으므로 루프 종료

        # GP 결과 감지 채널 확인 (신규 추가)
        detect_channel_id = config.get("DETECT_ID")
        if detect_channel_id and channel_id == detect_channel_id:
            # logging.info(f"Processing GP Result for {group_name}...") # 디버깅 로그 필요 시
            # await process_gp_result_message(message, config)
            return # 메시지 처리가 완료되었으므로 루프 종료

        # TODO: COMMAND 채널 처리 로직 추가 필요
        # command_channel_id = config.get("COMMAND_ID")
        # if command_channel_id and channel_id == command_channel_id:
        #     await process_command(message, config)
        #     return

# Placeholder for UserProfile and HeartbeatManager if they are not in the snippet
# Ensure these classes exist and have the methods used below (get_profile, save_profiles, get_last_heartbeat)
# --- 기존 UserProfile, HeartbeatManager 클래스 정의 부분 ---
# (이 부분은 수정되지 않았으므로 생략)
# class UserProfile: ...
# class HeartbeatManager: ...

# --- Friend List Generation Logic ---

# parse_pack_select 함수를 여기로 이동
def parse_pack_select(pack_select_str: str) -> list[str]:
    """pack_select 문자열을 파싱하여 유효한 팩 리스트 반환"""
    if not pack_select_str or pack_select_str == 'Unknown':
        return []
    packs = []
    valid_pack_names_lower = {vp.lower(): vp for vp in VALID_PACKS}
    for raw_pack in pack_select_str.split(','):
        lower_pack = raw_pack.strip().lower()
        if lower_pack in valid_pack_names_lower:
            packs.append(valid_pack_names_lower[lower_pack])
    return packs

async def generate_friend_list_files(group_friend_lists):
    """
    group_friend_lists를 기반으로 data/raw/ 디렉토리에
    "New" 와 "Old" 파일을 생성합니다.
    !!! 이 함수는 호출 전에 friend_list_lock을 획득해야 합니다 !!!
    group_friend_lists: {"New": [friend_code_list_new], "Old": [friend_code_list_old]}
    """
    raw_dir = os.path.join(DATA_PATH, "raw20")  # 20% 팩용 별도 디렉토리
    print(f"--- 그룹 친구 목록 파일 생성 시작 ({raw_dir}) ---")

    try:
        if os.path.exists(raw_dir):
            # 기존 New, Old 파일만 삭제 또는 전체 삭제 후 재생성
            # 여기서는 New, Old 파일만 대상으로 함
            for filename in ["New", "Old"]:
                file_path = os.path.join(raw_dir, filename)
                if os.path.exists(file_path):
                    try:
                        os.unlink(file_path)
                        # print(f"기존 파일 삭제: {file_path}")
                    except Exception as e:
                        print(f'파일 삭제 실패 {file_path}. 이유: {e}')
        else:
            os.makedirs(raw_dir, exist_ok=True)

        for group_name, friend_codes in group_friend_lists.items():
            if group_name not in ["New", "Old"]:
                logging.warning(f"알 수 없는 그룹 이름 '{group_name}'은 건너뜁니다.")
                continue

            file_path = os.path.join(raw_dir, group_name) # 파일 이름은 그룹 이름 (New 또는 Old)
            lines_for_file = []

            if friend_codes:
                lines_for_file.extend(friend_codes)
            else:
                lines_for_file.append("")

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines_for_file))
                # print(f"파일 생성 완료: {file_path}")
            except IOError as e:
                print(f"파일 쓰기 오류 ({file_path}): {e}")

        print(f"--- 그룹 친구 목록 파일 생성 완료 ---")

    except Exception as e:
        import traceback
        print(f"친구 목록 파일 생성 중 심각한 오류 발생: {e}")
        traceback.print_exc()

async def update_friend_lists(online_users_profiles):
    """
    온라인 유저 목록을 기반으로 "New" 그룹과 "Old" 그룹의 친구 코드 목록을 생성합니다.
    "Solgaleo" 또는 "Lunala" 팩을 선택한 사용자는 "New" 그룹으로, 그 외는 "Old" 그룹으로 분류됩니다.

    Args:
        online_users_profiles: 온라인 상태인 사용자들의 프로필 정보 딕셔너리.
            - key: 사용자 Discord ID (str)
            - value: 사용자 정보 딕셔너리 (pack_select, friend_code 등 포함)
    Returns:
        dict: {"New": [friend_code_list_new], "Old": [friend_code_list_old]}
    """
    print("--- 그룹별 친구 목록 생성 시작 (New/Old 분류) ---")
    friend_lists = {"New": [], "Old": []}
    if not online_users_profiles:
        print("온라인 유저가 없어 친구 목록 생성을 건너뜁니다.")
        return friend_lists

    new_group_packs = {"buzzwole"} # 비교를 위해 소문자로 설정

    for user_id, profile in online_users_profiles.items():
        user_name = profile.get('username', user_id)
        friend_code = profile.get('friend_code')
        pack_select_str = profile.get('pack_select', '').lower()

        if not friend_code:
            logging.debug(f"사용자 '{user_name}'의 친구 코드가 없어 목록에서 제외됩니다.")
            continue

        # 사용자의 pack_select 파싱 (쉼표로 구분된 여러 팩 가능성 고려)
        current_user_packs = {p.strip() for p in pack_select_str.split(',') if p.strip()}

        # New 그룹 조건: 선택한 팩 중 하나라도 new_group_packs에 포함되는 경우
        is_new_group = any(pack_name in new_group_packs for pack_name in current_user_packs)

        if is_new_group:
            friend_lists["New"].append(friend_code)
            logging.debug(f"사용자 '{user_name}' (팩: {pack_select_str}) New 그룹에 추가.")
        else:
            friend_lists["Old"].append(friend_code)
            logging.debug(f"사용자 '{user_name}' (팩: {pack_select_str}) Old 그룹에 추가.")

    print(f"--- 그룹별 친구 목록 생성 완료 ---")
    print(f"New 그룹 사용자 수: {len(friend_lists['New'])}")
    print(f"Old 그룹 사용자 수: {len(friend_lists['Old'])}")
    return friend_lists

# --- 최적화 로직 (Placeholder) ---
def calculate_optimized_lists(current_added_by_map, online_users_profiles):
    """ (Placeholder) 현재 친구 목록을 개선하는 로직. 실제 구현 필요. """
    print("--- 친구 목록 최적화 계산 시작 (Placeholder) ---")
    optimized_map = current_added_by_map.copy()
    print("--- 친구 목록 최적화 계산 완료 (Placeholder) ---")
    return optimized_map

async def optimize_and_apply_lists(initial_added_by_map, online_profiles):
    """ 최적화 계산 및 결과 적용 (변경 시에만 파일 생성) """
    if not initial_added_by_map or not online_profiles:
         print("최적화 건너뜀 (입력 데이터 부족)")
         return

    print("--- 유휴 시간 최적화 시작 ---")
    optimized_map = calculate_optimized_lists(initial_added_by_map, online_profiles)

    if optimized_map != initial_added_by_map:
        print("🔄 최적화 결과 변경점 발견! 새로운 친구 목록 적용 중...")
        async with friend_list_lock:
             await generate_friend_list_files(optimized_map, online_profiles)
        print("✅ 최적화된 친구 목록 적용 완료.")
    else:
        print(" değişiklik 없음. 최적화 결과 적용 안 함.")
    print("--- 유휴 시간 최적화 완료 ---")

# --- End Friend List Generation Logic ---

async def check_heartbeat_status():
    """주기적으로 메모리 기반 사용자 상태 확인 및 친구 목록 업데이트"""
    await bot.wait_until_ready()
    logging.info("⏳ 주기적 상태 확인 시작 대기 중 (초기 스캔 완료 후 진행)...")
    await initial_scan_complete_event.wait() # 기존 초기 스캔 완료 대기

    # 초기 스캔 완료 후 처음 실행 시에는 pastebin에서 사용자 정보 업데이트를 기다림 (기존 로직)
    # logging.info("⏳ Pastebin 사용자 정보 업데이트 대기 중...")
    # await asyncio.sleep(5)  # Pastebin 데이터 로딩을 위한 짧은 대기 시간 - 이 로직은 perform_initial_setup으로 이동됨

    # 백그라운드 초기화가 완료될 때까지 대기
    logging.info("⏳ 주기적 상태 확인 시작 대기 중 (백그라운드 초기화 완료 후 진행)...")
    await initialization_complete.wait()
    logging.info("▶️ 주기적 상태 확인 시작!")

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
            group_str = user_profile.group_name if user_profile.group_name else "그룹?"
            status_prefix = f"{display_name} ({discord_mention}, {code_str}, {group_str})"
            pack_select_str = user_profile.pack_select
            if isinstance(pack_select_str, list):
                pack_select_str = ','.join(pack_select_str) if pack_select_str else "?"
            status_suffix = f"(v:{user_profile.version}|t:{user_profile.type}|p:{pack_select_str}|b:{user_profile.barracks})"
            full_status_str = f"{status_prefix} {status_suffix}"

            is_online = False
            last_heartbeat_dt = None

            if test_flag:
                is_online = True
            else:
                latest_heartbeat_info = heartbeat_records.get(user_name)
                if latest_heartbeat_info and "latest_record" in latest_heartbeat_info:
                    latest_record = latest_heartbeat_info["latest_record"]
                    last_seen_iso = latest_record.get("timestamp")
                    latest_group = latest_heartbeat_info.get("source_group")
                    if latest_group and user_profile.group_name != latest_group:
                        user_profile.group_name = latest_group

                    if last_seen_iso:
                        try:
                            ts = datetime.fromisoformat(last_seen_iso.replace('Z', '+00:00'))
                            if ts.tzinfo is None: ts = ts.replace(tzinfo=timezone.utc)
                            last_heartbeat_dt = ts
                            if (now_utc - last_heartbeat_dt) <= offline_threshold:
                                is_online = True
                        except ValueError:
                             logging.warning(f"⚠️ 사용자 '{user_name}'의 잘못된 타임스탬프 형식 발견 (상태 확인 중): {last_seen_iso}")

            if is_online:
                online_users_status.append(f"🟢 {full_status_str}")

                if user_id_str:
                    # 친구 목록 생성에 필요한 정보 구성
                    current_online_profiles[user_id_str] = {
                         'username': display_name,
                         'barracks': user_profile.barracks,
                         'pack_select': user_profile.pack_select, # 올바른 pack_select 값 전달
                         'friend_code': user_profile.code,
                         'group_name': user_profile.group_name,
                         'custom_target_barracks': user_profile.custom_target_barracks,
                         'preferred_pack_order': user_profile.preferred_pack_order, # 팩 선호도 순서 전달
                         'graduated_packs': user_profile.graduated_packs, # <<< 누락된 라인 추가
                     }
                else:
                     print(f"  경고: 온라인 사용자 '{display_name}'의 Discord ID가 없어 친구 목록 생성에서 제외됩니다.")
            else:
                last_seen_str = last_heartbeat_dt.strftime('%Y-%m-%d %H:%M:%S') if last_heartbeat_dt else "기록 없음"
                offline_users_status.append(f"🔴 {full_status_str} [마지막: {last_seen_str}]")

        print(f"--- 확인 시간: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} ---")
        print(f"--- Online ({len(current_online_profiles)}명) ---")
        for status in online_users_status: print(f"  {status}")
        print(f"--- Offline ({len(offline_users_status)}명) ---")
        for status in offline_users_status: print(f"  {status}")
        print("----------------------------------------------")

        # --- 친구 목록 업데이트 및 최적화 로직 호출 ---
        # 주기적으로 Pastebin 데이터를 업데이트하여 최신 사용자 정보(Discord ID) 반영
        logging.info("🔄 주기적 Pastebin 사용자 정보 업데이트 시작...")
        await update_user_profiles_from_source()
        logging.info("✅ 주기적 Pastebin 사용자 정보 업데이트 완료.")

        # 수정된 update_friend_lists 호출
        group_based_friend_lists = await update_friend_lists(current_online_profiles)

        async with friend_list_lock:
             print("그룹 기반 친구 목록 파일 생성 시도...")
             # 수정된 generate_friend_list_files 호출 (current_online_profiles 인자 제거)
             await generate_friend_list_files(group_based_friend_lists)
             print("그룹 기반 친구 목록 파일 생성 완료.")

        # optimize_and_apply_lists 호출은 현재 새 요구사항과 맞지 않으므로 일단 주석 처리 또는 제거
        # await optimize_and_apply_lists(initial_map, current_online_profiles)

        print("--- 사용자 상태 확인 및 목록 업데이트 완료 ---")
        await asyncio.sleep(60)

# ... (GP 관련 함수들 복구 - parse_godpack_message, post_gp_result, process_gp_result_message)

async def parse_godpack_message(content: str) -> dict:
    """
    GP 결과 메시지 텍스트를 파싱하여 게시 정보와 태그 키를 반환합니다.
    Poke.py의 found_GodPack, found_Pseudo 역할을 가정하여 구현합니다.
    실제 메시지 형식에 따라 조정이 필요할 수 있습니다.

    Args:
        content: 메시지 텍스트 내용 (message.content)

    Returns:
        dict: {'inform': str | None, 'title': str | None, 'tag_key': str | None}
              inform: 게시될 본문 내용 (None이면 첨부파일만 게시)
              title: (포럼 스레드용) 제목
              tag_key: 적용할 태그의 키 (예: "1P", "2P", None)
    """
    logging.debug(f"GP 메시지 파싱 시작: {content[:100]}...")
    inform = None
    title = None
    tag_key = None

    try:
        username = None
        progress_percent = None
        player_count_tag = None
        timestamp_str = None

        user_match = re.search(r"^([\w\d_]+)\s+\(\d+\)", content, re.MULTILINE)
        if user_match: username = user_match.group(1)

        progress_match = re.search(r"\[(\d+)/(\d+)\]", content)
        if progress_match:
            try:
                current, total = int(progress_match.group(1)), int(progress_match.group(2))
                if total > 0: progress_percent = f"{int((current / total) * 100)}%"
            except (ValueError, ZeroDivisionError): logging.warning(f"진행률 계산 오류: {progress_match.group(0)}")

        player_count_match = re.search(r"\[(\dP)\]", content)
        if player_count_match: tag_key = player_count_match.group(1); player_count_tag = tag_key

        filename_match = re.search(r"File name: (\d{14})_", content)
        if filename_match:
            ts_digits = filename_match.group(1)
            try:
                dt_obj = datetime.strptime(ts_digits, '%Y%m%d%H%M%S')
                timestamp_str = dt_obj.strftime('%Y.%m.%d %H:%M')
            except ValueError: logging.warning(f"타임스탬프 변환 오류: {ts_digits}")

        if username and progress_percent and player_count_tag and timestamp_str:
            title = f"{username} / {progress_percent} / {player_count_tag} / {timestamp_str}"
        else:
            logging.warning(f"GP 메시지 파싱 중 일부 정보 누락. 제목 생성 실패. Content: {content[:100]}...")
            return {'inform': None, 'title': None, 'tag_key': None}

        logging.info(f"GP 메시지 파싱 결과: Title='{title}', Tag='{tag_key}'")
        return {'inform': inform, 'title': title, 'tag_key': tag_key}

    except Exception as e:
        logging.error(f"GP 메시지 파싱 중 오류 발생: {e}. Content: {content[:100]}...", exc_info=True)
        return {'inform': None, 'title': None, 'tag_key': None}

async def post_gp_result(posting_channel: discord.abc.GuildChannel, attachments: list[discord.Attachment], inform: str | None, title: str, tag_key: str | None, tags_config: dict, group_name: str):
    """파싱된 GP 결과와 첨부파일을 지정된 채널에 게시하고 태그를 적용합니다."""
    try:
        files_to_send = [await att.to_file() for att in attachments] if attachments else []

        if inform is None and files_to_send:
            logging.info(f"[{group_name}] 본문 없이 첨부파일({len(files_to_send)}개)만 포스팅합니다.")
            if isinstance(posting_channel, discord.ForumChannel):
                applied_tags_list = []
                yet_tag_id = tags_config.get("Yet")
                if yet_tag_id:
                    yet_tag = discord.utils.get(posting_channel.available_tags, id=yet_tag_id)
                    if yet_tag: applied_tags_list.append(yet_tag); logging.info(f"[{group_name}] 기본 태그 'Yet' 적용됨.")
                    else: logging.warning(f"[{group_name}] 'Yet' 태그(ID:{yet_tag_id}) 찾기 실패.")
                else: logging.warning(f"[{group_name}] 'Yet' 태그 미정의.")

                if tag_key and tag_key in tags_config:
                    tag_id = tags_config[tag_key]
                    target_tag_object = discord.utils.get(posting_channel.available_tags, id=tag_id)
                    if target_tag_object and target_tag_object not in applied_tags_list:
                         applied_tags_list.append(target_tag_object); logging.info(f"[{group_name}] 추가 태그 '{target_tag_object.name}' 적용됨.")
                    elif not target_tag_object: logging.warning(f"[{group_name}] 태그 키 '{tag_key}'(ID:{tag_id}) 태그 찾기 실패.")
                elif tag_key: logging.warning(f"[{group_name}] 태그 키 '{tag_key}' 미정의.")

                if not debug_flag:
                    await posting_channel.create_thread(name=title, files=files_to_send, applied_tags=applied_tags_list)
                    logging.info(f"[{group_name}] 포럼 채널 '{posting_channel.name}'에 첨부파일 스레드 생성 완료.")
                else:
                    logging.info(f"[{group_name}] [Debug Mode] 포럼 채널 '{posting_channel.name}'에 첨부파일 스레드 생성 건너뜀.")

            elif isinstance(posting_channel, discord.TextChannel):
                if not debug_flag:
                    await posting_channel.send(files=files_to_send)
                    logging.info(f"[{group_name}] 텍스트 채널 '{posting_channel.name}'에 첨부파일 전송 완료.")
                else:
                     logging.info(f"[{group_name}] [Debug Mode] 텍스트 채널 '{posting_channel.name}'에 첨부파일 전송 건너뜀.")
            else: logging.warning(f"[{group_name}] 포스팅 채널 타입 미지원 (첨부파일만 전송).")

        elif inform is not None:
            logging.info(f"[{group_name}] 본문과 첨부파일({len(files_to_send)}개) 포스팅합니다.")
            if isinstance(posting_channel, discord.ForumChannel):
                applied_tags_list = []
                if tag_key and tag_key in tags_config:
                    tag_id = tags_config[tag_key]
                    target_tag_object = discord.utils.get(posting_channel.available_tags, id=tag_id)
                    if target_tag_object: applied_tags_list.append(target_tag_object); logging.info(f"... 태그 '{target_tag_object.name}' 적용")
                    else: logging.warning(f"... 태그 ID({tag_id}) 찾기 실패")
                elif tag_key: logging.warning(f"... 태그 키 '{tag_key}' 정의 안됨")
                if not applied_tags_list:
                    yet_tag_id = tags_config.get("Yet")
                    if yet_tag_id:
                         yet_tag = discord.utils.get(posting_channel.available_tags, id=yet_tag_id)
                         if yet_tag: applied_tags_list.append(yet_tag); logging.info("... 기본 태그 'Yet' 적용")

                if not debug_flag:
                    await posting_channel.create_thread(name=title, content=inform, files=files_to_send, applied_tags=applied_tags_list)
                    logging.info(f"[{group_name}] 포럼 채널 '{posting_channel.name}'에 결과 스레드 생성 완료.")
                else:
                     logging.info(f"[{group_name}] [Debug Mode] 포럼 채널 '{posting_channel.name}'에 결과 스레드 생성 건너뜀.")

            elif isinstance(posting_channel, discord.TextChannel):
                if not debug_flag:
                    await posting_channel.send(content=inform, files=files_to_send)
                    logging.info(f"[{group_name}] 텍스트 채널 '{posting_channel.name}'에 결과 메시지 전송 완료.")
                else:
                    logging.info(f"[{group_name}] [Debug Mode] 텍스트 채널 '{posting_channel.name}'에 결과 메시지 전송 건너뜀.")
            else: logging.warning(f"[{group_name}] 포스팅 채널 타입 미지원.")

        else: logging.warning(f"[{group_name}] 포스팅할 내용(본문/첨부) 없음.")

    except discord.Forbidden: logging.error(f"[{group_name}] 포스팅 채널 '{posting_channel.name}' 권한 없음.")
    except discord.HTTPException as e: logging.error(f"[{group_name}] 포스팅 중 HTTP 오류: {e.status} {e.text}")
    except Exception as e: logging.error(f"[{group_name}] 포스팅 중 예상치 못한 오류: {e}", exc_info=True)

async def process_gp_result_message(message: discord.Message, group_config: dict):
    """GP 결과 메시지 처리 (텍스트 파싱, 포스팅, 태그 적용)"""
    group_name = group_config.get("NAME", "Unknown Group")
    content = message.content
    attachments = message.attachments
    logging.info(f"[{group_name}-Detect] GP 결과 메시지 감지 (ID: {message.id}), 첨부: {len(attachments)}개")
    logging.info(f"  Raw Content: {content[:200]}...")

    inform = None; title = None; tag_key = None

    if "Invalid" in content: logging.info(f"[{group_name}] 'Invalid' 키워드 감지. 건너뜁니다."); return
    elif "found by" in content: logging.info(f"[{group_name}] 'found by' 키워드 감지 (Pseudo GP)."); parsed_data = await parse_godpack_message(content)
    elif "Valid" in content: logging.info(f"[{group_name}] 'Valid' 키워드 감지 (Valid GP)."); parsed_data = await parse_godpack_message(content)
    else: logging.warning(f"[{group_name}] 유효 GP 키워드('Invalid', 'found by', 'Valid') 없음."); return

    if parsed_data: inform = parsed_data['inform']; title = parsed_data['title']; tag_key = parsed_data['tag_key']
    if title is None: logging.error(f"[{group_name}] 메시지 파싱 실패 (제목 없음)."); return

    posting_channel_id = group_config.get("POSTING_ID"); tags_config = group_config.get("TAGS", {})
    if not posting_channel_id: logging.warning(f"[{group_name}] 포스팅 채널 ID 없음."); return

    try: posting_channel = await bot.fetch_channel(posting_channel_id)
    except discord.NotFound: logging.error(f"[{group_name}] 포스팅 채널(ID: {posting_channel_id}) 찾기 실패."); return
    except discord.Forbidden: logging.error(f"[{group_name}] 포스팅 채널(ID: {posting_channel_id}) 접근 권한 없음."); return
    except Exception as e: logging.error(f"[{group_name}] 포스팅 채널(ID: {posting_channel_id}) 가져오기 오류: {e}", exc_info=True); return

    await post_gp_result(posting_channel=posting_channel, attachments=attachments, inform=inform, title=title, tag_key=tag_key, tags_config=tags_config, group_name=group_name)

async def main():
    """메인 실행 함수"""
    try:
        async with bot:
            bot.loop.create_task(check_heartbeat_status())
            await bot.start(DISCORD_TOKEN)
    except Exception as e:
        logging.critical(f"봇 실행 중 치명적인 오류 발생: {e}", exc_info=True)
    finally:
        logging.info("봇 종료.")

if __name__ == "__main__":
    asyncio.run(main())