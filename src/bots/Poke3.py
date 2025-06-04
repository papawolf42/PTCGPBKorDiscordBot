import discord
import asyncio
from datetime import datetime, timezone, timedelta
import json
import os
import re
import logging
import glob
from discord import app_commands

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# --- 상수 정의 ---
DISCORD_TOKEN = "***REMOVED***" # 실제 봇 토큰으로 변경 필요
# DATA_PATH 환경변수 사용
DATA_PATH = os.getenv('DATA_PATH', 'data')
VERIFIED_THREADS_FILE = os.path.join(DATA_PATH, "verified_threads.json") # 검증 스레드 데이터 저장 파일
DATA_DIR = DATA_PATH # 데이터 저장 폴더
DETECT_LOG_FILE_TEMPLATE = os.path.join(DATA_PATH, "detect_log_{group_name}.jsonl") # 그룹별 DETECT 채널 로그 파일
DETECT_LOG_LOAD_DAYS = 7 # 초기 로딩 시 가져올 최근 일수

# --- 그룹 설정 (GroupInfo.py 및 backup.py 기반) ---
GROUP_CONFIGS = [
    {
        "NAME": "Group1",
        "HEARTBEAT_ID": 1356173294939799634,
        "DETECT_ID": 1356173260730925272,
        "POSTING_ID": 1356176074169520150,
        "COMMAND_ID": 1356655918775013476,
        "MUSEUM_ID": 1356173214090530837,
        "TAGS": {
            "Yet": 1356631354720129094,
            "Good": 1356238509723353118,
            "Bad": 1356239240610058354,
            "1P": 1356237952937885858,
            "2P": 1356238101516783692,
            "3P": 1356238278021611570,
            "4P": 1356238320522498118,
            "5P": 1356238358405316688,
            "Notice": 1356239322847641710
        }
    },
    {
        "NAME": "Group3",
        "HEARTBEAT_ID": 1356173377500348457,
        "DETECT_ID": 1356173351781007360,
        "POSTING_ID": 1356176141404213360,
        "COMMAND_ID": 1356656594359681246,
        "MUSEUM_ID": 1356173340112457919,
        "TAGS": {
            "Yet": 1356632494124044308,
            "Good": 1356239558710267944,
            "Bad": 1356239589190140089,
            "1P": 1356239414526869726,
            "2P": 1356239437851529317,
            "3P": 1356239470562902186,
            "4P": 1356239498589245641,
            "5P": 1356239527185748058,
            "Notice": 1356239616801374392
        }
    },
    {
        "NAME": "Group6",
        "HEARTBEAT_ID": 1359071128018223348, # Heartbeat ID는 backup.py에 없으므로 Poke2.py 값 사용
        "DETECT_ID": 1359071093867941888,
        "POSTING_ID": 1359071042068549712,
        "COMMAND_ID": 1359130057083326564, # backup.py 값 사용
        "MUSEUM_ID": 1359071168509902920,
        "TAGS": {
            "Yet": 1359079239609225317,
            "Good": 1359079365480026162,
            "Bad": 1359079391346298880,
            "1P": 1359079402943676426,
            "2P": 1359079637006946434,
            "3P": 1359079608812572822,
            "4P": 1359079863780380722,
            "5P": 1359079889914822718,
            "Notice": 1359080105783066735
        }
    }
]

# --- 봇 설정 ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True # 메시지 내용 접근 권한
intents.guilds = True
intents.members = True # 멤버 관련 이벤트 처리 시 필요
intents.guild_messages = True # on_thread_create 등 guild 메시지 관련 이벤트에 필요

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# --- 전역 변수 ---
# 검증된 스레드 저장소: { group_name: {"Yet": {thread_id: {"name": str, "original_msg_id": int | None, "original_msg_content": str | None}}, ...} }
verified_threads = {config["NAME"]: {"Yet": {}, "Good": {}} for config in GROUP_CONFIGS}
verified_threads_lock = asyncio.Lock()

# DETECT 로그 파일 쓰기 락
detect_log_locks = {config["NAME"]: asyncio.Lock() for config in GROUP_CONFIGS}

# --- VIP ID 파일 생성 함수 추가 ---
VIP_IDS_FILE = os.path.join(DATA_DIR, "vip_ids.txt") # VIP ID 파일 경로 상수 추가

# --- 유틸리티 함수 ---
def ensure_data_dir(dir_path):
    """데이터 저장 디렉토리 확인 및 생성"""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            logging.info(f"📁 데이터 디렉토리 생성: {dir_path}")
        except OSError as e:
            logging.error(f"❌ 데이터 디렉토리 생성 실패: {e}", exc_info=True)
            raise

# --- 검증 스레드 데이터 처리 ---
def load_verified_threads():
    """(수정됨) JSON 파일에서 검증 스레드 데이터(원본 메시지 ID 및 내용 포함)를 로드합니다."""
    global verified_threads
    ensure_data_dir(DATA_DIR)
    if os.path.exists(VERIFIED_THREADS_FILE):
        try:
            with open(VERIFIED_THREADS_FILE, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                for group_name, statuses in loaded_data.items():
                    if group_name in verified_threads:
                        if isinstance(statuses, dict):
                            for status in ["Yet", "Good"]:
                                verified_threads[group_name][status] = {
                                    int(k): {
                                        "name": v.get("name"),
                                        "original_msg_id": v.get("original_msg_id"),
                                        "original_msg_content": v.get("original_msg_content") # 내용 로드 추가
                                    }
                                    for k, v in statuses.get(status, {}).items()
                                    if k.isdigit() and isinstance(v, dict)
                                }
                logging.info(f"💾 검증 스레드 데이터 로드 완료 (원본 ID/내용 포함): {VERIFIED_THREADS_FILE}")
        except json.JSONDecodeError:
            logging.warning(f"⚠️ 검증 스레드 파일 JSON 디코딩 오류: {VERIFIED_THREADS_FILE}. 초기 상태로 시작합니다.")
        except Exception as e:
            logging.error(f"❌ 검증 스레드 파일 읽기 오류: {e}", exc_info=True)
    else:
        logging.info("ℹ️ 검증 스레드 데이터 파일 없음. 새 파일 생성 예정.")

async def save_verified_threads():
    """(수정됨) 검증 스레드 데이터(원본 메시지 ID 포함)를 JSON 파일에 저장하고 VIP ID 파일을 생성합니다."""
    async with verified_threads_lock:
        ensure_data_dir(DATA_DIR)
        try:
            data_to_save = {}
            for group_name, statuses in verified_threads.items():
                data_to_save[group_name] = {}
                for status in ["Yet", "Good"]:
                    data_to_save[group_name][status] = {
                        str(thread_id): data # 키를 문자열로 변환
                        for thread_id, data in statuses.get(status, {}).items()
                    }

            temp_filepath = VERIFIED_THREADS_FILE + ".tmp"
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            os.replace(temp_filepath, VERIFIED_THREADS_FILE)
            # JSON 저장 후 VIP ID 파일 생성 호출
            await generate_vip_ids_file()
        except Exception as e:
            logging.error(f"❌ 검증 스레드 파일 쓰기 또는 VIP ID 파일 생성 오류: {e}", exc_info=True)
            if os.path.exists(temp_filepath):
                try: os.remove(temp_filepath)
                except OSError: pass

async def generate_vip_ids_file():
    """verified_threads 데이터에서 "Good" 및 "Yet" 상태의 스레드 정보를 파싱하여 vip_ids.txt 파일을 생성합니다."""
    logging.info(f"📄 VIP ID 파일 생성 시작 ({VIP_IDS_FILE})...")
    vip_lines = []
    # "Yet"과 "Good" 상태 모두 순회
    for status_to_process in ["Yet", "Good"]:
        for group_name, statuses in verified_threads.items():
            threads_in_status = statuses.get(status_to_process, {})
            for thread_id, data in threads_in_status.items():
                original_content = data.get("original_msg_content")
                if original_content:
                    # 정규식: 사용자 이름과 괄호 안의 16자리 ID 추출
                    match = re.search(r"([\w\d_]+)\s+\((\d{16})\)", original_content)
                    if match:
                        # 그룹 인덱스: 1=username, 2=vip_id
                        username = match.group(1)
                        vip_id = match.group(2)
                        # 출력 형식: vip_id | username
                        vip_lines.append(f"{vip_id} | {username}")
                    else:
                        # 파싱 실패 로그 (상태 정보 포함)
                        content_preview = original_content[:80].replace('\n', ' ')
                        logging.warning(f"[{group_name}-{status_to_process}] 스레드 ID {thread_id}의 original_msg_content 파싱 실패 (유저이름 (ID) 형식 불일치): {content_preview}...")
                else:
                    logging.debug(f"[{group_name}-{status_to_process}] 스레드 ID {thread_id}에 original_msg_content 없음.")

    # 중복 제거 및 정렬
    unique_vip_lines = sorted(list(set(vip_lines)))

    try:
        ensure_data_dir(DATA_DIR) # data 폴더 확인
        temp_filepath = VIP_IDS_FILE + ".tmp"
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unique_vip_lines))
        os.replace(temp_filepath, VIP_IDS_FILE)
        logging.info(f"✅ VIP ID 파일 생성 완료: {len(unique_vip_lines)} 라인 저장됨 ({VIP_IDS_FILE}).")
    except Exception as e:
        logging.error(f"❌ VIP ID 파일 쓰기 오류: {e}", exc_info=True)

async def save_verified_threads_periodically():
    """주기적으로 검증 스레드 데이터를 저장하는 태스크"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(300) # 5분마다 저장
        await save_verified_threads()
        logging.debug(f"🔄 주기적 데이터 저장 실행 ({VERIFIED_THREADS_FILE})")

# --- 검증 스레드 상태 업데이트 헬퍼 ---
async def _update_verified_threads(group_name: str, thread: discord.Thread, status: str | None):
    """(수정됨) verified_threads 딕셔너리에서 상태, 원본 메시지 ID 및 내용을 업데이트합니다."""
    if group_name not in verified_threads:
        logging.warning(f"[_update_verified_threads] 알 수 없는 그룹 이름: {group_name}")
        return

    thread_id = thread.id
    thread_name = thread.name
    original_msg_id = None
    original_msg_content = None # 내용 변수 추가

    # 상태가 "Yet" 또는 "Good"일 때만 원본 메시지 검색 시도
    if status in ["Yet", "Good"]:
        original_message_data = await find_original_message(group_name, thread_name)
        if original_message_data:
            original_msg_id = original_message_data.get("id")
            original_msg_content = original_message_data.get("content")
        else:
            logging.warning(f"⚠️ [{group_name}] 스레드 '{thread_name}'의 원본 메시지를 찾지 못했습니다.")

    async with verified_threads_lock:
        # 모든 상태에서 기존 스레드 정보 제거 (상태 변경 시 중복 방지)
        removed = False
        if thread_id in verified_threads[group_name]["Yet"]:
            del verified_threads[group_name]["Yet"][thread_id]
            removed = True
        if thread_id in verified_threads[group_name]["Good"]:
            del verified_threads[group_name]["Good"][thread_id]
            removed = True

        # 새로운 데이터 구조 생성
        thread_data = {
            "name": thread_name,
            "original_msg_id": original_msg_id,
            "original_msg_content": original_msg_content # 내용 추가
        }

        # 새로운 상태로 추가
        if status == "Yet":
            verified_threads[group_name]["Yet"][thread_id] = thread_data
            log_msg = f"➕ [{group_name}-Yet] 스레드 추가" if not removed else f"🔄 [{group_name}-Yet] 스레드 상태 변경"
            logging.info(f"{log_msg}: {thread_name} ({thread_id}), OrigID: {original_msg_id or 'Not Found'}")
        elif status == "Good":
            verified_threads[group_name]["Good"][thread_id] = thread_data
            log_msg = f"➕ [{group_name}-Good] 스레드 추가" if not removed else f"🔄 [{group_name}-Good] 스레드 상태 변경"
            logging.info(f"{log_msg}: {thread_name} ({thread_id}), OrigID: {original_msg_id or 'Not Found'}")
        elif removed: # status가 None이고 이전에 존재했을 경우 (삭제)
             logging.info(f"➖ [{group_name}] 스레드 제거됨: {thread_name} ({thread_id})")

    # 상태 업데이트 후 즉시 파일 저장
    await save_verified_threads()

# --- DETECT 채널 로그 처리 함수 ---
async def _append_to_detect_log(group_name: str, message_data: dict):
    """주어진 메시지 데이터를 해당 그룹의 로그 파일(.jsonl)에 추가합니다."""
    log_filepath = DETECT_LOG_FILE_TEMPLATE.format(group_name=group_name)
    lock = detect_log_locks.get(group_name)
    if not lock:
        logging.error(f"[_append_to_detect_log] 그룹 '{group_name}'의 락을 찾을 수 없습니다.")
        return

    async with lock:
        ensure_data_dir(DATA_DIR)
        try:
            with open(log_filepath, 'a', encoding='utf-8') as f:
                json.dump(message_data, f, ensure_ascii=False)
                f.write('\n') # 각 JSON 객체를 새 줄에 작성
            logging.debug(f"📝 [{group_name}] DETECT 로그 추가: ID {message_data.get('id')}")
        except Exception as e:
            logging.error(f"❌ [{group_name}] DETECT 로그 파일 쓰기 오류 ({log_filepath}): {e}", exc_info=True)

def _get_last_log_timestamp(group_name: str) -> datetime | None:
    """해당 그룹의 로그 파일에서 마지막 메시지의 타임스탬프를 읽습니다."""
    log_filepath = DETECT_LOG_FILE_TEMPLATE.format(group_name=group_name)
    if not os.path.exists(log_filepath):
        return None

    last_timestamp_str = None
    try:
        # 파일의 마지막 줄을 효율적으로 읽기 (파일이 매우 클 경우 대비)
        with open(log_filepath, 'rb') as f:
            try: # 마지막 줄 찾기 시도
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError: # 파일 시작까지 간 경우
                f.seek(0)
            last_line = f.readline().decode('utf-8')

        if last_line:
            last_data = json.loads(last_line)
            last_timestamp_str = last_data.get('timestamp')
            if last_timestamp_str:
                ts = datetime.fromisoformat(last_timestamp_str.replace('Z', '+00:00'))
                # 시간대가 없을 경우 UTC로 설정
                return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts

    except FileNotFoundError:
        return None # 파일 없음
    except Exception as e:
        logging.error(f"❌ [{group_name}] 마지막 로그 타임스탬프 읽기 오류 ({log_filepath}): {e}", exc_info=True)
        return None
    return None

async def _load_detect_logs_initial(group_name: str):
    """초기 실행 시 DETECT 채널 로그를 로드/업데이트합니다 (최근 N일 또는 마지막 이후)."""
    logging.info(f"⏳ [{group_name}] DETECT 채널 초기 로그 로딩 시작...")
    detect_channel_id = None
    for config in GROUP_CONFIGS:
        if config["NAME"] == group_name:
            detect_channel_id = config.get("DETECT_ID")
            break
    if not detect_channel_id:
        logging.error(f"[{group_name}] DETECT 채널 ID 설정 없음. 로그 로딩 건너뛰기.")
        return

    try:
        channel = await bot.fetch_channel(detect_channel_id)
        log_filepath = DETECT_LOG_FILE_TEMPLATE.format(group_name=group_name)
        ensure_data_dir(DATA_DIR)

        # 검색 시작 시점 결정
        after_time_utc: datetime | None = _get_last_log_timestamp(group_name)
        if after_time_utc:
            logging.info(f"  [{group_name}] 마지막 로그 시간 이후 메시지 로딩: {after_time_utc}")
        else:
            # 로그 파일이 없거나 마지막 시간 읽기 실패 시 최근 N일치 로딩
            after_time_utc = datetime.now(timezone.utc) - timedelta(days=DETECT_LOG_LOAD_DAYS)
            logging.info(f"  [{group_name}] 최근 {DETECT_LOG_LOAD_DAYS}일 메시지 로딩 (이후: {after_time_utc})")
            # 초기 로딩 시 기존 파일 삭제 (선택적)
            if os.path.exists(log_filepath):
                 try: os.remove(log_filepath); logging.info(f"  [{group_name}] 기존 로그 파일 삭제: {log_filepath}")
                 except OSError as e: logging.error(f"[{group_name}] 기존 로그 파일 삭제 실패: {e}")

        loaded_count = 0
        lock = detect_log_locks.get(group_name)
        if not lock:
            logging.error(f"[{group_name}] 락 찾기 실패. 로그 로딩 중단.")
            return

        async for message in channel.history(limit=None, after=after_time_utc, oldest_first=True):
            message_data = {
                "id": message.id,
                "content": message.content,
                "timestamp": message.created_at.replace(tzinfo=timezone.utc).isoformat(),
                "author_id": message.author.id
            }
            # 로그 파일에 직접 추가 (비동기 함수 호출)
            await _append_to_detect_log(group_name, message_data)
            loaded_count += 1
            if loaded_count % 500 == 0:
                logging.info(f"    [{group_name}] ... {loaded_count}개 메시지 로드 중 ...")
                await asyncio.sleep(0.1) # 짧은 sleep으로 부하 분산

        logging.info(f"✅ [{group_name}] DETECT 채널 초기 로그 로딩 완료 ({loaded_count}개 추가됨). 파일: {log_filepath}")

    except discord.NotFound:
        logging.error(f"❌ [{group_name}] DETECT 채널({detect_channel_id}) 찾기 실패.")
    except discord.Forbidden:
        logging.error(f"❌ [{group_name}] DETECT 채널({detect_channel_id}) 접근 권한 없음.")
    except Exception as e:
        logging.error(f"❌ [{group_name}] DETECT 채널 초기 로그 로딩 중 오류: {e}", exc_info=True)

# --- 원본 메시지 검색 함수 (파일 기반) ---
async def find_original_message(group_name: str, thread_title: str) -> dict | None:
    """(수정됨) 스레드 제목을 기반으로 로컬 로그 파일에서 원본 메시지 ID와 내용을 찾아 딕셔너리로 반환."""
    logging.debug(f"🔍 [{group_name}] 원본 메시지 검색 시작 (파일 기반) for: {thread_title}")

    # 1. 스레드 제목 파싱 (기존과 동일)
    match = re.match(r"(.+?)\s+(\d+)\s+/\s+(\d+%)\s+/\s+(\dP)\s+/\s+(\d{4}\.\d{2}\.\d{2})\s+(\d{2}:\d{2})", thread_title)
    if not match:
        logging.warning(f"[{group_name}] 스레드 제목 형식 분석 실패: {thread_title}")
        return None
    name, number, _, _, _, _ = match.groups()
    # Add the conditional logic
    if number == "000":
        search_key = name # 닉네임 뒤에 숫자가 없는 경우 (봇이 000 추가) 이름만으로 검색
    else:
        search_key = f"{name}{number}" # 원래 로직: 이름 + 숫자로 검색

    # 2. 로그 파일 경로 가져오기
    log_filepath = DETECT_LOG_FILE_TEMPLATE.format(group_name=group_name)
    if not os.path.exists(log_filepath):
        logging.warning(f"[{group_name}] 로그 파일 없음: {log_filepath}")
        return None

    # 3. 로그 파일 검색
    try:
        with open(log_filepath, 'r', encoding='utf-8') as f:
            # 순방향으로 라인을 읽도록 변경
            for line in f:
                try:
                    message_data = json.loads(line)
                    content = message_data.get("content", "")
                    # 검색 조건은 그대로 유지
                    if ("found by" in content or "Valid" in content) and search_key in content:
                        found_message_id = message_data.get("id")
                        if found_message_id:
                            logging.info(f"✅ [{group_name}] 파일에서 원본 메시지 찾음 (순방향 검색, ID: {found_message_id}) for: {thread_title}")
                            # ID와 content를 딕셔너리로 반환
                            return {"id": found_message_id, "content": content}
                except json.JSONDecodeError:
                    logging.warning(f"[{group_name}] 로그 파일 JSON 파싱 오류 무시: {line.strip()}")
                    continue
        # 파일을 끝까지 읽어도 찾지 못한 경우
        logging.warning(f"[{group_name}] 로그 파일에서 원본 메시지를 찾지 못함 (순방향 검색) for: {thread_title}")
        return None

    except Exception as e:
        logging.error(f"❌ [{group_name}] 로그 파일 검색 중 오류 ({log_filepath}): {e}", exc_info=True)
        return None

# --- 초기 스캔 함수 ---
async def initial_scan_verified_threads():
    """(수정됨) 봇 시작 시 스캔하여 Yet/Good 스레드, 원본 ID 및 내용을 verified_threads에 채웁니다."""
    logging.info("🔍 초기 검증 스레드 스캔 시작...")
    await bot.wait_until_ready()

    total_scanned = 0
    total_added = {"Yet": 0, "Good": 0}

    for config in GROUP_CONFIGS:
        group_name = config["NAME"]
        posting_channel_id = config.get("POSTING_ID")
        tags_config = config.get("TAGS", {})
        yet_tag_id = tags_config.get("Yet")
        good_tag_id = tags_config.get("Good")

        if not posting_channel_id or not yet_tag_id or not good_tag_id:
            logging.warning(f"[{group_name}] 포스팅 채널 ID 또는 Yet/Good 태그 ID가 설정되지 않아 스캔을 건너니다.")
            continue

        try:
            channel = await bot.fetch_channel(posting_channel_id)
            if not isinstance(channel, discord.ForumChannel):
                logging.warning(f"[{group_name}] 포스팅 채널({posting_channel_id})이 포럼 채널이 아닙니다. 스캔을 건너니다.")
                continue

            logging.info(f"  [{group_name}] 채널 스캔 중 ({posting_channel_id})...")
            scanned_in_channel = 0
            added_in_channel = {"Yet": 0, "Good": 0}

            # 활성 스레드 + 아카이브된 스레드 모두 가져오기
            threads_to_scan = channel.threads
            try:
                async for thread in channel.archived_threads(limit=None): # 모든 아카이브 스레드
                    threads_to_scan.append(thread)
            except discord.Forbidden:
                 logging.warning(f"[{group_name}] 아카이브된 스레드 접근 권한 없음. 활성 스레드만 스캔합니다.")
            except Exception as e:
                 logging.error(f"[{group_name}] 아카이브된 스레드 가져오기 중 오류: {e}")

            async with verified_threads_lock: # 스캔 중 업데이트 방지
                verified_threads[group_name]["Yet"].clear()
                verified_threads[group_name]["Good"].clear()

                for thread in threads_to_scan:
                    scanned_in_channel += 1
                    total_scanned += 1
                    applied_tag_ids = {tag.id for tag in thread.applied_tags}

                    current_status = None
                    if yet_tag_id in applied_tag_ids:
                        current_status = "Yet"
                    elif good_tag_id in applied_tag_ids:
                        current_status = "Good"

                    if current_status:
                        # 각 스레드에 대해 원본 메시지 검색 (ID 및 내용)
                        original_message_data = await find_original_message(group_name, thread.name)
                        original_msg_id = None
                        original_msg_content = None
                        if original_message_data:
                            original_msg_id = original_message_data.get("id")
                            original_msg_content = original_message_data.get("content")

                        thread_data = {
                            "name": thread.name,
                            "original_msg_id": original_msg_id,
                            "original_msg_content": original_msg_content # 내용 추가
                        }
                        verified_threads[group_name][current_status][thread.id] = thread_data

                        if current_status == "Yet": total_added["Yet"] += 1; added_in_channel["Yet"] += 1
                        else: total_added["Good"] += 1; added_in_channel["Good"] += 1

                        if scanned_in_channel % 50 == 0: # 로그 빈도 줄임
                            logging.info(f"    [{group_name}] {scanned_in_channel}개 스레드 스캔/검색 중... (현재 OrigID: {original_msg_id or 'Not Found'})")
                            await asyncio.sleep(0.1) # API 검색 부하 분산

            logging.info(f"    [{group_name}] 스캔 완료: {scanned_in_channel}개 스캔, Yet {added_in_channel['Yet']}개, Good {added_in_channel['Good']}개 추가.")

        except discord.NotFound:
            logging.error(f"❌ [{group_name}] 포스팅 채널({posting_channel_id})을 찾을 수 없습니다.")
        except discord.Forbidden:
            logging.error(f"❌ [{group_name}] 포스팅 채널({posting_channel_id})에 접근할 권한이 없습니다.")
        except Exception as e:
            logging.error(f"❌ [{group_name}] 채널 스캔 중 예상치 못한 오류 발생: {e}", exc_info=True)

    logging.info(f"✅ 초기 검증 스레드 스캔 완료: 총 {total_scanned}개 스캔, Yet {total_added['Yet']}개, Good {total_added['Good']}개 추가.")
    # 초기 스캔 후 데이터 저장 (VIP ID 파일 생성은 save_verified_threads 내부에서 처리됨)
    await save_verified_threads()

# --- 이벤트 핸들러 및 주기적 작업 ---
@bot.event
async def on_ready():
    """봇 준비 완료 시 실행"""
    logging.info(f'✅ 로그인됨: {bot.user}')

    # 기존 verified_threads 데이터 로드
    load_verified_threads()

    # 명령어 트리 동기화 (주석 처리됨)
    # YOUR_TEST_SERVER_ID = 123456789012345678 # << 중요: 실제 테스트 서버 ID로 변경하세요!
    # test_guild = discord.Object(id=YOUR_TEST_SERVER_ID)
    # try:
    #     await tree.sync(guild=test_guild)
    #     logging.info(f"🌳 테스트 서버({YOUR_TEST_SERVER_ID})에 슬래시 명령어 동기화 완료.")
    # except Exception as e:
    #     logging.error(f"❌ 슬래시 명령어 동기화 실패: {e}", exc_info=True)

    # 각 그룹별 DETECT 채널 로그 초기 로딩 실행
    for config in GROUP_CONFIGS:
        bot.loop.create_task(_load_detect_logs_initial(config["NAME"]))

    # 초기 스캔 및 주기적 저장 태스크 시작
    bot.loop.create_task(initial_scan_verified_threads())
    bot.loop.create_task(save_verified_threads_periodically())

    logging.info("--- 봇 초기화 완료 (로그 로딩 진행 중) ---")

@bot.event
async def on_thread_create(thread: discord.Thread):
    """스레드 생성 시 verified_threads 업데이트"""
    # ForumChannel 내의 스레드만 처리
    if not isinstance(thread.parent, discord.ForumChannel):
        return

    parent_channel_id = thread.parent_id
    group_name = None
    yet_tag_id = None
    good_tag_id = None

    # 해당 채널이 어떤 그룹의 포스팅 채널인지 확인
    for config in GROUP_CONFIGS:
        if config.get("POSTING_ID") == parent_channel_id:
            group_name = config["NAME"]
            tags_config = config.get("TAGS", {})
            yet_tag_id = tags_config.get("Yet")
            good_tag_id = tags_config.get("Good")
            break

    if not group_name or not yet_tag_id or not good_tag_id:
        return # 설정된 그룹의 포스팅 채널이 아니거나 태그 ID가 없으면 무시

    applied_tag_ids = {tag.id for tag in thread.applied_tags}
    new_status = None
    if yet_tag_id in applied_tag_ids:
        new_status = "Yet"
    elif good_tag_id in applied_tag_ids:
        new_status = "Good"

    if new_status:
        await _update_verified_threads(group_name, thread, new_status)
        # 생성 시에는 별도 저장을 하지 않음 (주기적 저장 또는 다른 이벤트에서 처리)

@bot.event
async def on_thread_update(before: discord.Thread, after: discord.Thread):
    """스레드 업데이트 시(태그 변경 등) verified_threads 업데이트"""
    # ForumChannel 내의 스레드만 처리
    if not isinstance(after.parent, discord.ForumChannel):
        return

    # 아카이브 상태 변경은 무시 (스캔 시 처리됨)
    if before.archived != after.archived:
        return

    # 태그 변경이 없으면 무시 (성능 최적화)
    if before.applied_tags == after.applied_tags:
        return

    parent_channel_id = after.parent_id
    group_name = None
    yet_tag_id = None
    good_tag_id = None

    # 해당 채널이 어떤 그룹의 포스팅 채널인지 확인
    for config in GROUP_CONFIGS:
        if config.get("POSTING_ID") == parent_channel_id:
            group_name = config["NAME"]
            tags_config = config.get("TAGS", {})
            yet_tag_id = tags_config.get("Yet")
            good_tag_id = tags_config.get("Good")
            break

    if not group_name or not yet_tag_id or not good_tag_id:
        return # 설정된 그룹의 포스팅 채널이 아니거나 태그 ID가 없으면 무시

    applied_tag_ids = {tag.id for tag in after.applied_tags}
    current_status = None
    if yet_tag_id in applied_tag_ids:
        current_status = "Yet"
    elif good_tag_id in applied_tag_ids:
        current_status = "Good"

    # 상태 변경이 있을 경우에만 업데이트
    await _update_verified_threads(group_name, after, current_status)
    # 업데이트 시에는 별도 저장을 하지 않음 (주기적 저장 또는 다른 이벤트에서 처리)

@bot.event
async def on_thread_delete(thread: discord.Thread):
    """스레드 삭제 시 verified_threads 업데이트"""
    # ForumChannel 내의 스레드만 처리
    if not isinstance(thread.parent, discord.ForumChannel):
        return

    parent_channel_id = thread.parent_id
    group_name = None

    # 해당 채널이 어떤 그룹의 포스팅 채널인지 확인
    for config in GROUP_CONFIGS:
        if config.get("POSTING_ID") == parent_channel_id:
            group_name = config["NAME"]
            break

    if not group_name:
        return # 설정된 그룹의 포스팅 채널이 아니면 무시

    # status를 None으로 전달하여 제거
    await _update_verified_threads(group_name, thread, None)
    # 삭제 시에는 별도 저장을 하지 않음 (주기적 저장 또는 다른 이벤트에서 처리)

@bot.event
async def on_disconnect():
    """봇 연결 끊김 시 데이터 저장 시도"""
    logging.warning("🔌 봇 연결 끊김 감지. 데이터 저장 시도...")
    await save_verified_threads()
    logging.info("💾 연결 끊김 전 데이터 저장 완료.")

@bot.event
async def on_message(message: discord.Message):
    """메시지 수신 시 DETECT 채널 로그 업데이트"""
    if message.author == bot.user: return # 봇 메시지 무시

    channel_id = message.channel.id
    group_name = None

    # 해당 채널이 어떤 그룹의 DETECT 채널인지 확인
    for config in GROUP_CONFIGS:
        if config.get("DETECT_ID") == channel_id:
            group_name = config["NAME"]
            break

    if group_name:
        # DETECT 채널 메시지이면 로그 파일에 추가
        message_data = {
            "id": message.id,
            "content": message.content,
            "timestamp": message.created_at.replace(tzinfo=timezone.utc).isoformat(),
            "author_id": message.author.id
        }
        await _append_to_detect_log(group_name, message_data)

    # 명령어 처리 (만약 command_prefix를 사용한다면)
    # await bot.process_commands(message)

# --- 메인 실행 ---
async def main():
    """메인 실행 함수"""
    try:
        async with bot:
            await bot.start(DISCORD_TOKEN)
    except Exception as e:
        logging.critical(f"봇 실행 중 치명적인 오류 발생: {e}", exc_info=True)
        # 종료 전 마지막 저장 시도
        await save_verified_threads()
    finally:
        logging.info("봇 종료.")

if __name__ == "__main__":
    asyncio.run(main()) 