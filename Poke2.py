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

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# --- 상수 정의 ---
YOUR_TEST_SERVER_ID = os.getenv('DISCORD_SERVER_ID') # 실제 테스트 서버 ID


# Heartbeat 관련 채널 (기존)
GROUP1_CHANNEL_ID = os.getenv('DISCORD_GROUP1_HEARTBEAT_ID')
GROUP3_CHANNEL_ID = os.getenv('DISCORD_GROUP3_HEARTBEAT_ID')
HEARTBEAT_TARGET_CHANNEL_IDS = {GROUP1_CHANNEL_ID: "Group1", GROUP3_CHANNEL_ID: "Group3"} # 이름 변경: Heartbeat 채널임을 명시

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN') # 봇 토큰

HEARTBEAT_DATA_DIR = "data/heartbeat_data" # 데이터 저장 폴더
USER_DATA_DIR = "data/user_data" # 사용자 프로필 데이터 저장 폴더
USER_INFO_SOURCE_URL = "os.getenv('PASTEBIN_URL')" # 사용자 정보 소스 URL
TARGET_BARRACKS_DEFAULT = 170 # 기본 목표 배럭 정의

# 팩 선호도 기본 순서
DEFAULT_PACK_ORDER = ["Shining", "Arceus", "Palkia", "Dialga", "Mew", "Pikachu", "Charizard", "Mewtwo"]
# 유효한 팩 목록 (자동완성 및 검증용)
VALID_PACKS = DEFAULT_PACK_ORDER[:] # 기본 순서를 복사하여 사용, 필요시 확장

# 오류 감지 및 알림 채널 (기존 ERROR_DETECT_CHANNEL_ID)
GODPACK_WEBHOOK_CHANNEL_ID = os.getenv('DISCORD_GROUP6_DETECT_ID')
BARRACKS_REDUCTION_STEP = 5 # 한 번에 줄일 목표 배럭 수
MIN_TARGET_BARRACKS = 100 # 최소 목표 배럭 (더 이상 줄이지 않음)

# --- 그룹 설정 (newGroup.py 정보 기반) ---
GROUP_CONFIGS = [
    {
        "NAME": "Group1",
        "HEARTBEAT_ID": os.getenv('DISCORD_GROUP1_HEARTBEAT_ID'),
        "DETECT_ID": os.getenv('DISCORD_GROUP1_DETECT_ID'),
        "POSTING_ID": os.getenv('DISCORD_GROUP1_POSTING_ID'),
        "COMMAND_ID": os.getenv('DISCORD_GROUP1_COMMAND_ID'),
        "MUSEUM_ID": os.getenv('DISCORD_GROUP1_MUSEUM_ID'),
        "TAGS": {
            "Yet": os.getenv('DISCORD_GROUP1_TAG_YET'),
            "Good": os.getenv('DISCORD_GROUP1_TAG_GOOD'),
            "Bad": os.getenv('DISCORD_GROUP1_TAG_BAD'),
            "1P": os.getenv('DISCORD_GROUP1_TAG_1P'),
            "2P": os.getenv('DISCORD_GROUP1_TAG_2P'),
            "3P": os.getenv('DISCORD_GROUP1_TAG_3P'),
            "4P": os.getenv('DISCORD_GROUP1_TAG_4P'),
            "5P": os.getenv('DISCORD_GROUP1_TAG_5P'),
            "Notice": os.getenv('DISCORD_GROUP1_TAG_NOTICE')
        }
    },
    {
        "NAME": "Group3",
        "HEARTBEAT_ID": os.getenv('DISCORD_GROUP3_HEARTBEAT_ID'),
        "DETECT_ID": os.getenv('DISCORD_GROUP3_DETECT_ID'),
        "POSTING_ID": os.getenv('DISCORD_GROUP3_POSTING_ID'),
        "COMMAND_ID": os.getenv('DISCORD_GROUP3_COMMAND_ID'),
        "MUSEUM_ID": os.getenv('DISCORD_GROUP3_MUSEUM_ID'),
        "TAGS": {
            "Yet": os.getenv('DISCORD_GROUP3_TAG_YET'),
            "Good": os.getenv('DISCORD_GROUP3_TAG_GOOD'),
            "Bad": os.getenv('DISCORD_GROUP3_TAG_BAD'),
            "1P": os.getenv('DISCORD_GROUP3_TAG_1P'),
            "2P": os.getenv('DISCORD_GROUP3_TAG_2P'),
            "3P": os.getenv('DISCORD_GROUP3_TAG_3P'),
            "4P": os.getenv('DISCORD_GROUP3_TAG_4P'),
            "5P": os.getenv('DISCORD_GROUP3_TAG_5P'),
            "Notice": os.getenv('DISCORD_GROUP3_TAG_NOTICE')
        }
    },
    {
        "NAME": "Group6",
        "HEARTBEAT_ID": os.getenv('DISCORD_GROUP6_HEARTBEAT_ID'), # Heartbeat (예시, 실제 그룹 ID에 맞게 조정 필요)
        "DETECT_ID": os.getenv('DISCORD_GROUP6_DETECT_ID'), # GP webhook
        "POSTING_ID": os.getenv('DISCORD_GROUP6_POSTING_ID'),
        "COMMAND_ID": 1356656481180848195, # Group6 COMMAND_ID 추가 (Poke3.py에 없음, Poke2.py 값 유지)
        "MUSEUM_ID": os.getenv('DISCORD_GROUP6_MUSEUM_ID'),
        "TAGS": {
            "Yet": os.getenv('DISCORD_GROUP6_TAG_YET'),
            "Good": os.getenv('DISCORD_GROUP6_TAG_GOOD'),
            "Bad": os.getenv('DISCORD_GROUP6_TAG_BAD'),
            "1P": os.getenv('DISCORD_GROUP6_TAG_1P'),
            "2P": os.getenv('DISCORD_GROUP6_TAG_2P'),
            "3P": os.getenv('DISCORD_GROUP6_TAG_3P'),
            "4P": os.getenv('DISCORD_GROUP6_TAG_4P'),
            "5P": os.getenv('DISCORD_GROUP6_TAG_5P'),
            "Notice": os.getenv('DISCORD_GROUP6_TAG_NOTICE')
        }
    }
    # 다른 그룹 설정을 여기에 딕셔너리로 추가
    # {
    #     "NAME": "Group7", ...
    # },
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
            'preferred_pack_order': self.preferred_pack_order, # 추가
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
    파일 로드 시 custom_target_barracks 키가 없으면 기본값(TARGET_BARRACKS_DEFAULT)을 추가하고 파일을 업데이트합니다.
    preferred_pack_order 키가 없거나 None이면 사용자의 pack_select를 최우선으로, 나머지는 랜덤 순서로 생성하여 추가하고 파일을 업데이트합니다.
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

        user = User.from_dict(data)
        if user:
            # --- 파일 업데이트 (필요한 경우) ---
            if needs_update:
                logging.info(f"  💾 사용자 '{user_name}' 프로필 파일 업데이트 (custom_target_barracks 또는 preferred_pack_order 추가/수정됨).")
                if not write_user_profile(user): # 수정된 user 객체를 다시 저장
                    logging.warning(f"⚠️ 사용자 '{user_name}' 프로필 파일 업데이트 실패: {filepath}")
                    # 업데이트 실패해도 로드된 user 객체는 반환
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
        # 그룹 이름 추출 ("Group6-Heartbeat" -> "Group6" 또는 채널 이름 그대로)
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
                channel = await bot.fetch_channel(channel_id)
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

            except discord.NotFound:
                logging.error(f"❌ 채널을 찾을 수 없음: {group_name} ({channel_id})")
            except discord.Forbidden:
                logging.error(f"❌ 채널 접근 권한 없음: {group_name} ({channel_id})")
            except Exception as e:
                logging.error(f"❌ 채널 '{group_name}' 스캔 중 오류 발생: {e}")
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

    # 기존 TARGET_CHANNEL_IDS 기반 Heartbeat 처리 (하위 호환 또는 다른 그룹용으로 남겨둘 수 있음)
    # 만약 GROUP_CONFIGS가 모든 Heartbeat 채널을 포함한다면 아래 코드는 제거 가능
    if channel_id in HEARTBEAT_TARGET_CHANNEL_IDS:
        channel_id_str = str(channel_id)
        channel_name = HEARTBEAT_TARGET_CHANNEL_IDS[channel_id]
        await process_heartbeat_message(message, channel_id_str, channel_name)
        return

# Placeholder for UserProfile and HeartbeatManager if they are not in the snippet
# Ensure these classes exist and have the methods used below (get_profile, save_profiles, get_last_heartbeat)
# --- 기존 UserProfile, HeartbeatManager 클래스 정의 부분 ---
# (이 부분은 수정되지 않았으므로 생략)
# class UserProfile: ...
# class HeartbeatManager: ...

# --- Friend List Generation Logic ---
async def generate_friend_list_files(added_by_map, user_profiles_for_gen):
    """
    계산된 added_by_map을 기반으로 data/raw/ 디렉토리에
    {username}_added_by 와 {username} 파일을 생성합니다.
    !!! 이 함수는 호출 전에 friend_list_lock을 획득해야 합니다 !!!
    user_profiles_for_gen: { user_id_str: { ..., 'custom_target_barracks': int | None, 'pack_select': str, 'preferred_pack_order': list[str] } }
    added_by_map: { u_id_str: [v1_id_str, v2_id_str...] }
    """
    raw_dir = "data/raw"
    print(f"--- 친구 목록 파일 생성 시작 ({raw_dir}) ---")

    try:
        if os.path.exists(raw_dir):
            for filename in os.listdir(raw_dir):
                file_path = os.path.join(raw_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f'파일 삭제 실패 {file_path}. 이유: {e}')
        else:
            os.makedirs(raw_dir, exist_ok=True)

        add_list = {user_id: [] for user_id in user_profiles_for_gen}

        for u_id_str, added_by_user_ids in added_by_map.items():
            u_profile_info = user_profiles_for_gen.get(u_id_str)
            if not u_profile_info: continue

            # --- 사용자별 목표 배럭 결정 (파일 출력용) ---
            custom_target_u = u_profile_info.get('custom_target_barracks')
            display_target_barracks = TARGET_BARRACKS_DEFAULT
            if custom_target_u is not None and isinstance(custom_target_u, int) and custom_target_u > 0:
                display_target_barracks = custom_target_u
            # --- 사용자별 목표 배럭 결정 끝 ---

            display_name_u = u_profile_info.get('username', u_id_str)
            safe_display_name_u = sanitize_filename(display_name_u)
            added_by_path = os.path.join(raw_dir, f"{safe_display_name_u}_added_by")

            # --- 친구 목록 데이터 준비 (정렬용) ---
            friend_lines_data = []
            total_barracks_for_u = 0
            for v_id_str in added_by_user_ids:
                v_profile_info = user_profiles_for_gen.get(v_id_str)
                if not v_profile_info: continue

                friend_data = {
                    'code': v_profile_info.get('friend_code', '코드없음'),
                    'username': v_profile_info.get('username', v_id_str),
                    'group': v_profile_info.get('group_name', '?'),
                    'barracks': v_profile_info.get('barracks', 0),
                    'pack_select': v_profile_info.get('pack_select', '?')
                }
                friend_lines_data.append(friend_data)
                total_barracks_for_u += friend_data['barracks']

            # --- 친구 목록 정렬 (Current Pack 기준) ---
            # 사용자(u_id_str)의 선호 팩 순서 가져오기 (없으면 기본값)
            u_preferred_order = u_profile_info.get('preferred_pack_order')
            # 유효성 검사 및 기본값 설정 (get_safe_preferred_order 로직 간소화 버전)
            if not u_preferred_order or not isinstance(u_preferred_order, list):
                effective_preferred_order = DEFAULT_PACK_ORDER[:]
            else:
                # 누락된 팩 추가 로직 (선택적, 필요 시 추가)
                # current_packs_in_order = set(u_preferred_order)
                # missing_packs = [p for p in VALID_PACKS if p not in current_packs_in_order]
                # if missing_packs:
                #     effective_preferred_order = u_preferred_order + missing_packs
                # else:
                effective_preferred_order = u_preferred_order[:]

            def sort_key(friend_data):
                pack_select_str = friend_data.get('pack_select', '')
                selected_packs_raw = [p.strip() for p in pack_select_str.split(',') if p.strip()]

                selected_packs = []
                valid_pack_names_lower = {vp.lower(): vp for vp in VALID_PACKS}
                for raw_pack in selected_packs_raw:
                    lower_pack = raw_pack.lower()
                    if lower_pack in valid_pack_names_lower:
                        selected_packs.append(valid_pack_names_lower[lower_pack])

                min_index = float('inf')
                num_packs = float('inf')
                username = friend_data.get('username', '') # 동률 처리용

                if not selected_packs or selected_packs == ['Unknown']:
                    pass
                else:
                    num_packs = len(selected_packs)
                    current_min_index = float('inf')
                    for pack in selected_packs:
                        try:
                            # *** 변경점: effective_preferred_order (사용자 선호도) 사용 ***
                            index = effective_preferred_order.index(pack)
                            if index < current_min_index:
                                current_min_index = index
                        except ValueError:
                            continue # 사용자의 선호 목록에 없는 팩은 무시 (또는 기본 순서 인덱스 사용?)
                    min_index = current_min_index

                # (가장 높은 우선순위 팩의 인덱스, 팩 개수, 사용자 이름) 순으로 정렬
                return (min_index, num_packs, username)

            friend_lines_data.sort(key=sort_key)
            # --- 정렬 끝 ---

            # --- 파일 내용 생성 --- 
            lines_for_added_by_file = []
            lines_for_added_by_file.append(f"Max Target Barracks: {display_target_barracks}")
            # 사용자 본인 정보 추가
            u_barracks = u_profile_info.get('barracks', '?')
            u_current_pack = u_profile_info.get('pack_select', '?')
            u_group_name = u_profile_info.get('group_name', '?')
            lines_for_added_by_file.append(f"My Info: Username: {display_name_u} / Group: {u_group_name} / Barracks: {u_barracks} / Current Pack: {u_current_pack}")
            # 사용자 선호 팩 순서 추가
            u_preferred_order = u_profile_info.get('preferred_pack_order')
            if u_preferred_order and isinstance(u_preferred_order, list):
                order_str = ", ".join(u_preferred_order)
                lines_for_added_by_file.append(f"My Pack Preference: {order_str}")
            else:
                default_order_str = ", ".join(DEFAULT_PACK_ORDER)
                lines_for_added_by_file.append(f"My Pack Preference: Default ({default_order_str})")
            lines_for_added_by_file.append("")
            lines_for_added_by_file.append("Friend Code\tUsername\tGroup\tBarracks\tCurrent Pack")
            lines_for_added_by_file.append("-----------\t--------\t-----\t--------\t------------")

            # 정렬된 친구 목록 추가
            for friend_data in friend_lines_data:
                line = f"{friend_data['code']}\t{friend_data['username']}\t{friend_data['group']}\t{friend_data['barracks']}\t{friend_data['pack_select']}"
                lines_for_added_by_file.append(line)

            lines_for_added_by_file.append("-----------\t--------\t-----\t--------\t------------")
            lines_for_added_by_file.append(f"Total Added Friend Barracks:\t{total_barracks_for_u}")
            # --- 파일 내용 생성 끝 ---

            try:
                with open(added_by_path, 'w', encoding='utf-8') as f: f.write('\n'.join(lines_for_added_by_file))
            except IOError as e: print(f"파일 쓰기 오류 ({added_by_path}): {e}"); continue

            u_friend_code = u_profile_info.get('friend_code')
            if not u_friend_code: continue

            # u_id_str을 추가한 사용자 목록(added_by_user_ids)을 순회
            for v_id_str in added_by_user_ids:
                # v_id_str (추가한 사람)의 추가 목록(add_list)에
                # u_id_str (추가된 사람)의 코드를 추가합니다.
                # 자기 자신(v_id_str == u_id_str)의 코드도 포함됩니다.
                if v_id_str in add_list: # v_id가 add_list에 있는지 확인
                   add_list[v_id_str].append(u_friend_code)

        for v_id_str, friend_codes_to_add in add_list.items():
             v_profile_info = user_profiles_for_gen.get(v_id_str)
             if v_profile_info:
                 display_name_v = v_profile_info.get('username', v_id_str)
                 safe_display_name_v = sanitize_filename(display_name_v)
                 add_list_path = os.path.join(raw_dir, f"{safe_display_name_v}")
                 try:
                     with open(add_list_path, 'w', encoding='utf-8') as f: f.write('\n'.join(friend_codes_to_add))
                 except IOError as e: print(f"파일 쓰기 오류 ({add_list_path}): {e}")

    except Exception as e:
        import traceback
        print(f"친구 목록 파일 생성 중 심각한 오류 발생: {e}")
        traceback.print_exc()

async def update_friend_lists(online_users_profiles):
    """
    온라인 유저 목록을 기반으로 초기 친구 추가 목록({username}_added_by)을 계산합니다.
    사용자별 custom_target_barracks를 우선 적용하고, 없으면 TARGET_BARRACKS_DEFAULT를 사용합니다.
    사용자의 preferred_pack_order(팩 선호도)와 다른 사용자의 add_count(추가된 횟수)를 기준으로
    목표 배럭을 채울 때까지 친구를 선택하여 추가합니다. 그룹 정보는 친구 선택에 사용되지 않습니다.

    Args:
        online_users_profiles: 온라인 상태인 사용자들의 프로필 정보 딕셔너리.
            - key: 사용자 Discord ID (str)
            - value: 사용자 정보 딕셔너리 (barracks, pack_select, friend_code, group_name, custom_target_barracks, preferred_pack_order 등 포함)
    Returns:
        dict: 계산된 added_by_map. 각 사용자가 추가해야 할 친구들의 Discord ID 리스트.
            - key: 사용자 Discord ID (str)
            - value: 해당 사용자가 추가할 친구 Discord ID 리스트 (자기 자신 포함)
    """
    print("--- 초기 친구 목록 계산 시작 ---")
    added_by_map = {}
    if not online_users_profiles:
        print("온라인 유저가 없어 초기 목록 계산을 건너뜁니다.")
        return added_by_map

    # --- 사용될 상수 및 헬퍼 함수 ---
    # DEFAULT_PACK_ORDER 는 전역 상수 사용
    def get_safe_preferred_order(profile):
        """프로필에서 preferred_pack_order를 안전하게 가져옵니다. 없으면 기본 순서를 반환합니다."""
        order = profile.get('preferred_pack_order')
        # 프로필에 저장된 순서가 VALID_PACKS의 모든 팩을 포함하는지 확인하고, 누락된 팩은 뒤에 추가 (순서 유지)
        if order and isinstance(order, list):
            current_packs_in_order = set(order)
            missing_packs = [p for p in VALID_PACKS if p not in current_packs_in_order]
            # 누락된 팩이 있다면 기존 순서 뒤에 추가 (순서는 VALID_PACKS 기준)
            if missing_packs:
                 return order + missing_packs
            return order[:]
        else:
            return DEFAULT_PACK_ORDER[:]

    online_user_ids = list(online_users_profiles.keys())
    total_barracks_all_online = sum(profile.get('barracks', 0) for profile in online_users_profiles.values())
    print(f"온라인 유저 수: {len(online_user_ids)}, 총 배럭: {total_barracks_all_online}, 기본 목표 배럭: {TARGET_BARRACKS_DEFAULT}")

    # --- 그룹별 배럭 현황 계산 및 출력 ---
    group_barracks = {"Group1": 0, "Group3": 0, "Group6": 0, "Other": 0, "Unknown": 0}
    for profile in online_users_profiles.values():
        group = profile.get('group_name')
        barracks = profile.get('barracks', 0)
        if group in group_barracks: group_barracks[group] += barracks
        elif group: group_barracks["Other"] += barracks
        else: group_barracks["Unknown"] += barracks

    print("그룹별 온라인 배럭 현황:")
    for group, barracks in group_barracks.items():
        if barracks > 0 or group in ["Group1", "Group3", "Group6"]:
            print(f"  - {group}: {barracks} 배럭")
    # --- 그룹별 배럭 현황 계산 및 출력 끝 ---

    # 초기화: 각 유저는 자기 자신을 먼저 추가
    added_by_map = {user_id: [user_id] for user_id in online_user_ids}
    # 각 유저가 몇 번 추가되었는지 카운트 (자기 자신은 카운트하지 않음)
    add_count = {user_id: 0 for user_id in online_user_ids}

    if total_barracks_all_online < TARGET_BARRACKS_DEFAULT:
        print(f"시나리오 1 추정: 총 배럭({total_barracks_all_online}) < 기본 목표({TARGET_BARRACKS_DEFAULT}). 모든 유저가 서로 추가 시도.")
        for u_id in online_user_ids:
            # 자기 자신을 제외한 모든 온라인 유저 ID 추가
            other_users = [v_id for v_id in online_user_ids if u_id != v_id]
            added_by_map[u_id].extend(other_users)
            # 추가된 다른 유저들의 add_count 증가
            for v_id in other_users:
                add_count[v_id] = add_count.get(v_id, 0) + 1
    else:
        print(f"시나리오 2/3: 총 배럭 >= 기본 목표. 유저별 목록 계산 시작...")

        # --- 친구 선택 로직 헬퍼 함수 --- (팩 선호도 기반으로 수정)
        def add_friends_from_candidates(candidates_to_consider: list[str], u_preferred_order: list[str], current_barracks: int, effective_target: int, current_added_ids: list[str], add_cnt: dict, profiles: dict):
            """
            주어진 후보 목록에서 팩 선호도와 add_count를 기준으로 친구를 추가합니다.
            """
            new_barracks = current_barracks
            if new_barracks >= effective_target:
                return new_barracks, current_added_ids

            # 후보자들을 (우선순위_팩, 우선순위_add_count, user_id) 튜플 리스트로 변환
            candidate_details = []
            for v_id in candidates_to_consider:
                # 이미 추가된 유저는 제외
                if v_id in current_added_ids: continue
                v_profile = profiles.get(v_id)
                if v_profile:
                    v_pack_select = v_profile.get('pack_select', 'Unknown') # 후보자의 현재 팩
                    v_add_count = add_cnt.get(v_id, 0)

                    # 우선순위 계산: 요청자의 선호 팩 목록에서의 인덱스
                    try:
                        pack_priority = u_preferred_order.index(v_pack_select)
                    except ValueError:
                        pack_priority = float('inf') # 선호 목록에 없으면 최하 순위

                    candidate_details.append((pack_priority, v_add_count, v_id))
                else:
                    logging.warning(f"add_friends_from_candidates: 후보자 프로필 누락 ({v_id})")

            # 정렬: 1순위: pack_priority (오름차순, 선호도 높을수록 작음), 2순위: add_count (오름차순)
            candidate_details.sort()

            # 정렬된 후보자 리스트를 순회하며 친구 추가
            for _, _, v_id in candidate_details:
                if new_barracks >= effective_target: break # 목표 도달 시 중단

                v_profile = profiles.get(v_id)
                if v_profile:
                    v_barracks = v_profile.get('barracks', 0)
                    # 목표 배럭을 초과하지 않는 경우에만 추가
                    # 단, 아직 아무도 추가 안 했고 이 후보를 추가해야 목표를 넘더라도 추가 (최소 1명 보장 시도)
                    can_add = (new_barracks + v_barracks <= effective_target) or \
                              (len(current_added_ids) == 1 and new_barracks < effective_target)

                    if can_add:
                        current_added_ids.append(v_id)
                        new_barracks += v_barracks
                        add_cnt[v_id] = add_cnt.get(v_id, 0) + 1
                else:
                    pass # 프로필 누락 로그는 위에서 처리

            return new_barracks, current_added_ids
        # --- 헬퍼 함수 정의 끝 ---

        # --- 각 온라인 유저에 대해 친구 목록 계산 --- (로직 동일, 헬퍼 함수 수정됨)
        for u_id in online_user_ids:
            u_profile = online_users_profiles[u_id]

            # 사용자별 유효 목표 배럭 결정
            custom_target = u_profile.get('custom_target_barracks')
            effective_target_barracks = TARGET_BARRACKS_DEFAULT
            if custom_target is not None and isinstance(custom_target, int) and custom_target > 0:
                 effective_target_barracks = custom_target

            u_group = u_profile.get('group_name')
            u_preferred_order = get_safe_preferred_order(u_profile)
            current_barracks = u_profile.get('barracks', 0) # 본인 배럭부터 시작
            current_added_by_ids = added_by_map[u_id][:] # 초기 상태 (자기 자신만 포함된 리스트 복사)

            # --- 친구 후보 리스트 생성 (그룹 분류 없이) ---
            all_candidates = [v_id for v_id in online_user_ids if u_id != v_id] # 자기 자신 제외
            # --- 친구 후보 리스트 생성 끝 ---

            # --- 친구 추가 시도 (그룹 우선순위 없이 단일 리스트 사용) ---
            if current_barracks < effective_target_barracks and all_candidates: # 후보가 있을 때만 시도
                current_barracks, current_added_by_ids = add_friends_from_candidates(
                    all_candidates, # 그룹 분류 없는 전체 후보 리스트 전달
                    u_preferred_order,
                    current_barracks,
                    effective_target_barracks,
                    current_added_by_ids, # 기존에 추가된 ID 목록 전달 (add_friends_from_candidates가 수정하도록)
                    add_count,
                    online_users_profiles
                )

            # 최종 추가된 친구 목록 저장
            added_by_map[u_id] = current_added_by_ids

    print("--- 초기 친구 목록 계산 완료 ---")
    return added_by_map

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

        initial_map = await update_friend_lists(current_online_profiles)

        async with friend_list_lock:
             print("기본 친구 목록 파일 생성 시도...")
             await generate_friend_list_files(initial_map, current_online_profiles)
             print("기본 친구 목록 파일 생성 완료.")

        await optimize_and_apply_lists(initial_map, current_online_profiles)

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

# --- 슬래시 명령어 정의 ---

@bot.tree.command(name="내정보", description="내 프로필 정보를 확인합니다.")
async def my_profile_info(interaction: discord.Interaction):
    """사용자 본인의 프로필 정보를 보여주는 슬래시 명령어"""
    user_id_str = str(interaction.user.id)
    target_user_profile: User | None = None
    target_user_name = "Unknown"

    # 메모리에서 사용자 찾기
    for user_name, profile in user_profiles.items():
        if profile.discord_id == user_id_str:
            target_user_profile = profile
            target_user_name = user_name
            break

    if target_user_profile:
        logging.info(f"Slash Command: /myinfo by {interaction.user.name} ({user_id_str}) - 사용자 찾음: {target_user_name}") # 명령어 이름 로그 수정
        # Embed 사용하여 깔끔하게 표시 (선택 사항)
        embed = discord.Embed(title=f"{target_user_name}님의 프로필 정보", color=discord.Color.blue())
        embed.add_field(name="Discord ID", value=target_user_profile.discord_id or "N/A", inline=False)
        embed.add_field(name="친구 코드", value=target_user_profile.code or "N/A", inline=False)
        embed.add_field(name="배럭 수", value=str(target_user_profile.barracks), inline=True)
        # custom_target_barracks 표시 (None이면 기본값 사용 문구 표시)
        if target_user_profile.custom_target_barracks is not None:
            target_display = f"{target_user_profile.custom_target_barracks}"
        else:
            target_display = f"설정 안됨 (기본값 {TARGET_BARRACKS_DEFAULT} 사용)"
        embed.add_field(name="목표 배럭", value=target_display, inline=True)

        # --- 그룹 이름 매핑 ---
        group_name = target_user_profile.group_name
        display_group_name = "N/A" # 기본값
        if group_name == "Group1":
            display_group_name = "샤이닝"
        elif group_name == "Group3":
            display_group_name = "모든팩"
        elif group_name == "Group6":
            display_group_name = "PTCGPBKor"
        elif group_name: # 정의되지 않은 다른 그룹 이름이 있는 경우
            display_group_name = group_name
        # --- 그룹 이름 매핑 끝 ---

        embed.add_field(name="그룹", value=display_group_name, inline=True) # 매핑된 이름 사용
        embed.add_field(name="버전", value=target_user_profile.version, inline=True)
        embed.add_field(name="타입", value=target_user_profile.type, inline=True)
        embed.add_field(name="개봉 팩", value=target_user_profile.pack_select or "N/A", inline=True)
        # --- 팩선호도 추가 ---
        preferred_order_display = "설정 안됨"
        if target_user_profile.preferred_pack_order:
            # 리스트를 문자열로 변환 (예: "Shining, Arceus, Palkia, ...")
            # 너무 길어질 수 있으므로 최대 8개만 표시하고 나머지는 '...' 처리
            display_list = target_user_profile.preferred_pack_order[:8]
            preferred_order_display = ", ".join(display_list)
            if len(target_user_profile.preferred_pack_order) > 8:
                preferred_order_display += ", ..."
        embed.add_field(name="팩선호도", value=preferred_order_display, inline=False) # inline=False로 설정하여 다음 줄에 표시
        # --- 팩선호도 추가 끝 ---
        embed.set_footer(text="이 메시지는 당신에게만 보입니다.")

        if not debug_flag:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        logging.warning(f"Slash Command: /myinfo by {interaction.user.name} ({user_id_str}) - 사용자 데이터 없음") # 명령어 이름 로그 수정
        if not debug_flag:
            await interaction.response.send_message("당신의 프로필 정보를 찾을 수 없습니다. Heartbeat 정보가 먼저 기록되어야 할 수 있습니다.", ephemeral=True)

@bot.tree.command(name="목표배럭설정", description="내 목표 배럭 수를 설정합니다.")
@app_commands.describe(barracks="설정할 목표 배럭 수 (예: 160)")
async def set_target_barracks(interaction: discord.Interaction, barracks: int):
    """사용자 본인의 custom_target_barracks 값을 수정하는 슬래시 명령어"""
    user_id_str = str(interaction.user.id)
    target_user_profile: User | None = None
    target_user_name = "Unknown"

    # 입력값 기본 검증 (0 이하 또는 너무 큰 값 방지 - 예: 500 초과)
    if barracks <= 0 or barracks > 500:
        if not debug_flag:
            await interaction.response.send_message(f"목표 배럭 수는 1 이상 500 이하의 값이어야 합니다.", ephemeral=True)
        return

    # 메모리에서 사용자 찾기
    for user_name, profile in user_profiles.items():
        if profile.discord_id == user_id_str:
            target_user_profile = profile
            target_user_name = user_name
            break

    if target_user_profile:
        logging.info(f"Slash Command: /목표배럭설정 by {interaction.user.name} ({user_id_str}) - 사용자: {target_user_name}, 요청 값: {barracks}")
        old_value = target_user_profile.custom_target_barracks
        effective_old_value = old_value if old_value is not None else TARGET_BARRACKS_DEFAULT

        target_user_profile.custom_target_barracks = barracks

        # 파일 저장 시도
        if write_user_profile(target_user_profile):
            logging.info(f"  - 사용자 '{target_user_name}' 프로필 업데이트 성공.")
            # ephemeral=True 추가하여 본인에게만 보이도록 변경
            if not debug_flag:
                await interaction.response.send_message(f"✅ **{interaction.user.mention}** 님의 목표 배럭 수가 `{effective_old_value}`에서 `{barracks}`(으)로 성공적으로 변경되었습니다.", ephemeral=True)
        else:
            logging.error(f"  - 사용자 '{target_user_name}' 프로필 업데이트 실패.")
            # 실패 시 메모리 값 롤백 (선택 사항)
            target_user_profile.custom_target_barracks = old_value
            # ephemeral=True 추가하여 본인에게만 보이도록 변경
            if not debug_flag:
                await interaction.response.send_message(f"❌ **{interaction.user.mention}** 님의 목표 배럭 수를 변경하는 중 오류가 발생했습니다. 파일 저장에 실패했습니다.", ephemeral=True)
    else:
        # 프로필 못찾은 에러는 계속 ephemeral 유지
        logging.warning(f"Slash Command: /setbarracks by {interaction.user.name} ({user_id_str}) - 사용자 데이터 없음") # 명령어 이름 로그 수정
        if not debug_flag:
            await interaction.response.send_message("당신의 프로필 정보를 찾을 수 없어 목표 배럭을 설정할 수 없습니다. Heartbeat 정보가 먼저 기록되어야 할 수 있습니다.", ephemeral=True)

# /팩선호도 명령어 자동완성 함수
async def pack_autocomplete_placeholder(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    choices = [pack for pack in VALID_PACKS if current.lower() in pack.lower()]
    return [app_commands.Choice(name=choice, value=choice) for choice in choices[:25]]

@bot.tree.command(name="팩선호도", description="선호하는 팩 순서 설정 (최대 4개)")
@app_commands.describe(
    pack1="1순위 선호 팩",
    pack2="2순위 선호 팩 (선택)",
    pack3="3순위 선호 팩 (선택)",
    pack4="4순위 선호 팩 (선택)"
)
@app_commands.autocomplete(pack1=pack_autocomplete_placeholder, pack2=pack_autocomplete_placeholder, pack3=pack_autocomplete_placeholder, pack4=pack_autocomplete_placeholder)
# @app_commands.guilds(YOUR_TEST_SERVER_ID)
async def set_preferred_packs(
    interaction: discord.Interaction,
    pack1: str,
    pack2: str = None,
    pack3: str = None,
    pack4: str = None
):
    """팩선호도 명령어 Placeholder"""
    preferred_packs = [p for p in [pack1, pack2, pack3, pack4] if p is not None]

    # 간단한 유효성 검사 (예: 중복 확인 - 필요시 추가)
    if not preferred_packs: # pack1은 필수이므로 이 경우는 사실상 없음
        if not debug_flag:
            await interaction.response.send_message("적어도 1개의 팩을 선택해야 합니다.", ephemeral=True)
        return

    # 선택된 팩들이 유효한지 확인 (VALID_PACKS에 있는지)
    invalid_packs = [p for p in preferred_packs if p not in VALID_PACKS]
    if invalid_packs:
        if not debug_flag:
            await interaction.response.send_message(f"유효하지 않은 팩 이름이 포함되어 있습니다: {', '.join(invalid_packs)}", ephemeral=True)
        return

    # 중복 확인
    if len(preferred_packs) != len(set(preferred_packs)):
        if not debug_flag:
            await interaction.response.send_message(f"중복된 팩 이름이 있습니다. 각 팩은 한 번만 선택해주세요.", ephemeral=True)
        return

    logging.info(f"✅ /팩선호도 명령어 호출됨 (사용자: {interaction.user.name}, 값: {preferred_packs})")

    # --- 사용자 프로필 찾기 ---
    user_id_str = str(interaction.user.id)
    target_user_profile: User | None = None
    target_user_name = "Unknown"

    for user_name, profile in user_profiles.items():
        if profile.discord_id == user_id_str:
            target_user_profile = profile
            target_user_name = user_name
            break

    if not target_user_profile:
        logging.warning(f"Slash Command: /팩선호도 by {interaction.user.name} ({user_id_str}) - 사용자 데이터 없음")
        if not debug_flag:
            await interaction.response.send_message("당신의 프로필 정보를 찾을 수 없어 팩 선호도를 설정할 수 없습니다. Heartbeat 정보가 먼저 기록되어야 할 수 있습니다.", ephemeral=True)
        return
    # --- 사용자 프로필 찾기 끝 ---

    # --- 새로운 선호도 순서 생성 ---
    new_preferred_order = preferred_packs[:] # 사용자가 선택한 팩으로 시작 (복사본 사용)
    chosen_packs_set = set(new_preferred_order) # 빠른 확인을 위해 set 사용

    # 기본 팩 순서를 순회하며 사용자가 선택하지 않은 팩 추가
    for default_pack in DEFAULT_PACK_ORDER:
        if default_pack not in chosen_packs_set:
            new_preferred_order.append(default_pack)
    # --- 새로운 선호도 순서 생성 끝 ---

    old_order = target_user_profile.preferred_pack_order # 롤백용 기존 순서 저장

    # 프로필 업데이트
    target_user_profile.preferred_pack_order = new_preferred_order

    # 파일 저장 시도
    if write_user_profile(target_user_profile):
        logging.info(f"  - 사용자 '{target_user_name}' 프로필 업데이트 성공 (팩 선호도 변경).")
        # 변경된 순서 표시 (최대 8개)
        display_order = ", ".join(new_preferred_order[:8])
        if len(new_preferred_order) > 8: display_order += ", ..."
        if not debug_flag:
            await interaction.response.send_message(f"✅ **{interaction.user.mention}** 님의 팩 선호도 순서가 성공적으로 변경되었습니다:\n`{display_order}`", ephemeral=True)
    else:
        logging.error(f"  - 사용자 '{target_user_name}' 프로필 업데이트 실패 (팩 선호도 변경).")
        # 실패 시 메모리 값 롤백
        target_user_profile.preferred_pack_order = old_order
        if not debug_flag:
            await interaction.response.send_message(f"❌ **{interaction.user.mention}** 님의 팩 선호도를 변경하는 중 오류가 발생했습니다. 파일 저장에 실패했습니다.", ephemeral=True)

if __name__ == "__main__":
    asyncio.run(main())