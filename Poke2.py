import discord
import asyncio
from datetime import datetime, timezone, timedelta
import json
import os
import re # 정규표현식 사용
import shutil # 폴더 스캔용

# Group1과 Group3의 채널 ID (Poke.py 참조)
GROUP1_CHANNEL_ID = os.getenv('DISCORD_GROUP1_HEARTBEAT_ID')
GROUP3_CHANNEL_ID = os.getenv('DISCORD_GROUP3_HEARTBEAT_ID')

TARGET_CHANNEL_IDS = {
    GROUP1_CHANNEL_ID: "Group1",
    GROUP3_CHANNEL_ID: "Group3"
}

# 봇 토큰 (Poke.py 참조)
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Heartbeat 데이터 저장 폴더
HEARTBEAT_DATA_DIR = "heartbeat_data"

# 봇 인텐트 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True # history fetching might need this

# 봇 클라이언트 초기화
bot = discord.Client(intents=intents)

# 사용자별 최신 heartbeat 기록 (메모리)
# 구조: {user_name: {"latest_record": dict, "channel_id_str": str}}
# latest_record 구조: {"timestamp": iso_str, "barracks": int, ..., "channel_id_str": str}
heartbeat_records = {}

# --- 데이터 로드/저장 함수 ---

def ensure_data_dir():
    """데이터 저장 디렉토리가 있는지 확인하고 없으면 생성합니다."""
    if not os.path.exists(HEARTBEAT_DATA_DIR):
        try:
            os.makedirs(HEARTBEAT_DATA_DIR)
            print(f"📁 데이터 디렉토리 생성: {HEARTBEAT_DATA_DIR}")
        except OSError as e:
            print(f"❌ 데이터 디렉토리 생성 실패: {e}")
            # 심각한 오류일 수 있으므로 봇 종료 또는 다른 처리 필요
            raise

def sanitize_filename(name):
    """사용자 이름을 안전한 파일명으로 변환합니다."""
    # 간단하게 슬래시, 백슬래시, 콜론 등 일반적인 경로 문자를 제거/교체
    # 필요에 따라 더 정교한 정규화 로직 추가 가능
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    # 파일명 길이 제한 (OS별 상이)
    return name[:100] # 예시로 100자 제한

def get_user_filepath(user_name):
    """사용자 이름에 해당하는 JSON 파일 경로를 반환합니다."""
    safe_name = sanitize_filename(user_name)
    return os.path.join(HEARTBEAT_DATA_DIR, f"{safe_name}.json")

def read_user_data(user_name):
    """사용자 JSON 파일을 읽어 기록 리스트를 반환합니다. 파일 없으면 빈 리스트 반환."""
    filepath = get_user_filepath(user_name)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # 데이터 로드 시 간단한 유효성 검사 (각 항목이 dict이고 timestamp 있는지)
                    valid_data = [r for r in data if isinstance(r, dict) and 'timestamp' in r]
                    # 로드 시 정렬 보장
                    valid_data.sort(key=lambda x: x.get('timestamp', ''))
                    return valid_data
                else:
                    print(f"⚠️ 사용자 '{user_name}'의 파일 형식이 리스트가 아님: {filepath}. 빈 리스트 반환.")
                    return [] # 잘못된 형식은 빈 리스트로 처리
        except json.JSONDecodeError:
            print(f"⚠️ 사용자 '{user_name}'의 파일 JSON 디코딩 오류: {filepath}. 빈 리스트 반환.")
            # 손상된 파일 처리: 백업 또는 삭제 고려
            return []
        except Exception as e:
            print(f"❌ 사용자 '{user_name}' 파일 읽기 오류: {e}")
            return []
    else:
        return [] # 파일 없으면 빈 리스트

def write_user_data(user_name, data_list):
    """사용자 기록 리스트(정렬된 상태)를 JSON 파일에 씁니다."""
    filepath = get_user_filepath(user_name)
    try:
        # 쓰기 전 최종 정렬 보장
        data_list.sort(key=lambda x: x.get('timestamp', ''))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ 사용자 '{user_name}' 파일 쓰기 오류: {e}")
        return False

def load_all_latest_user_data():
    """데이터 폴더에서 모든 사용자 파일의 최신 기록을 읽어 메모리에 로드합니다."""
    global heartbeat_records
    ensure_data_dir()
    print(f"💾 데이터 폴더 스캔 및 최신 기록 로드 시작: {HEARTBEAT_DATA_DIR}")
    loaded_records = {}
    try:
        for filename in os.listdir(HEARTBEAT_DATA_DIR):
            if filename.endswith(".json"):
                # 파일명에서 사용자 이름 복원 시도 (sanitize_filename 역함수 필요? 일단은 확장자 제거)
                user_name_from_file = filename[:-5] # .json 제거
                user_data = read_user_data(user_name_from_file) # 정렬된 리스트 반환
                if user_data: # 데이터가 있으면
                    latest_record = user_data[-1] # 마지막 항목이 최신
                    # 메모리 구조에 맞게 저장
                    channel_id_str = latest_record.get('channel_id_str') # 기록에서 채널 ID 가져오기
                    if channel_id_str:
                         loaded_records[user_name_from_file] = {
                             "latest_record": latest_record,
                             "channel_id_str": channel_id_str
                         }
                    else:
                        print(f"⚠️ 사용자 '{user_name_from_file}'의 최신 기록에 channel_id_str 없음. 스킵됨.")

    except FileNotFoundError:
        print(f"ℹ️ 데이터 디렉토리를 찾을 수 없음: {HEARTBEAT_DATA_DIR}")
    except Exception as e:
        print(f"❌ 최신 기록 로드 중 오류 발생: {e}")

    heartbeat_records = loaded_records
    print(f"✅ 최신 기록 로드 완료: {len(heartbeat_records)}명")

def parse_heartbeat_message(content):
    """메시지 내용에서 heartbeat 관련 정보를 추출합니다."""
    data = {
        'barracks': 0,
        'version': 'Unknown',
        'type': 'Unknown',
        'select': 'Unknown'
    }

    # Online: 사용자 및 배럭 수 추출
    online_line = None
    for line in content.splitlines():
        # Use strip() before lower() and startswith() for robustness
        if line.strip().lower().startswith("online:"):
            online_line = line.strip() # Use the stripped line
            break

    if online_line:
        # Find all numbers AFTER "Online:" on that line
        # This avoids issues with stopping at first comma/period
        # We count all sequences of digits on the found line.
        # e.g., "Online: Main, 1, 2, 3." -> finds '1', '2', '3' -> count = 3
        # e.g., "Online: Main." -> finds nothing -> count = 0
        numbers_in_line = re.findall(r'\b\d+\b', online_line)
        # Count how many numbers were found
        data['barracks'] = len(numbers_in_line)

    # Version 추출
    version_match = re.search(r"^Version:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    if version_match:
        data['version'] = version_match.group(1).strip()

    # Type 추출
    type_match = re.search(r"^Type:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    if type_match:
        data['type'] = type_match.group(1).strip()

    # Select 추출
    select_match = re.search(r"^Select:\s*(.*?)\s*$", content, re.MULTILINE | re.IGNORECASE)
    if select_match:
        data['select'] = select_match.group(1).strip()

    return data

async def process_heartbeat_message(message, channel_id_str, channel_name):
    """Heartbeat 메시지를 처리하여 사용자 파일에 저장하고 메모리 최신 기록을 업데이트합니다."""
    if "Online:" in message.content:
        try:
            user_name = message.content.split("\n")[0].strip()
            if not user_name: # 사용자 이름이 비어있는 경우 스킵
                 print(f"⚠️ [{channel_name}] 에서 사용자 이름을 추출할 수 없음 (빈 이름): {message.content[:50]}...")
                 return False

            timestamp_dt = message.created_at.replace(tzinfo=timezone.utc) # UTC로 명시적 변환
            timestamp_iso = timestamp_dt.isoformat()

            # 상세 정보 추출
            parsed_data = parse_heartbeat_message(message.content)
            # 채널 ID 추가
            parsed_data['channel_id_str'] = channel_id_str

            # 최근 데이터 레코드 생성
            recent_record = {
                "timestamp": timestamp_iso,
                **parsed_data # 추출된 데이터 병합
            }

            # --- 사용자 파일 업데이트 ---
            user_data = read_user_data(user_name) # 기존 기록 읽기 (리스트)

            # 중복 타임스탬프 확인
            if any(record.get('timestamp') == timestamp_iso for record in user_data):
                # print(f"ℹ️ 중복 Heartbeat 감지됨 [{channel_name}]: {user_name} at {timestamp_iso}")
                # 중복 시 파일 업데이트 및 메모리 업데이트 불필요, 그러나 최신 상태 유지를 위해 메모리는 업데이트할 수도 있음
                # 일단은 중복이면 아무것도 안 함
                pass
            else:
                user_data.append(recent_record) # 새 기록 추가
                # 파일 쓰기 (write_user_data 내부에서 정렬됨)
                if write_user_data(user_name, user_data):
                    # 로그 출력 시 UTC ISO 문자열 그대로 사용
                    print(f"💾 Heartbeat 기록됨 [{channel_name}]: {user_name} ({parsed_data['barracks']} barracks) at {timestamp_iso}")
                    # 파일 저장 성공 시 메모리 업데이트
                    heartbeat_records[user_name] = {
                        "latest_record": recent_record,
                        "channel_id_str": channel_id_str
                    }
                    return True # 변경사항 있음 (메모리 기준)

            # 메모리 업데이트 여부와 관계없이 파일 처리 결과를 반환할 수도 있음
            # 현재는 메모리가 업데이트되었을 때만 True 반환
            return False # 중복이거나 파일 쓰기 실패 시

        except IndexError:
            print(f"⚠️ [{channel_name}] 에서 사용자 이름을 추출할 수 없는 Online 메시지 형식: {message.content[:50]}...")
        except Exception as e:
            print(f"❌ [{channel_name}] 에서 Heartbeat 처리 중 오류 발생: {e} | 메시지: {message.content[:100]}...")
    return False # Heartbeat 메시지가 아니거나 처리 중 오류 발생 시 변경 없음

# --- 이벤트 핸들러 및 주기적 작업 ---

@bot.event
async def on_ready():
    """봇이 준비되었을 때 실행되는 이벤트 핸들러"""
    print(f'✅ 로그인됨: {bot.user}')
    ensure_data_dir() # 데이터 디렉토리 확인/생성

    # 시작 시 데이터 로드 전에 메시지 출력
    print("💾 데이터 로딩 시작...")
    load_all_latest_user_data()

    # --- 전체 기록 중 가장 마지막 타임스탬프 찾기 ---
    overall_latest_timestamp = None
    if heartbeat_records: # 메모리에 로드된 기록이 있는 경우
        for user_name, data in heartbeat_records.items():
            latest_record = data.get("latest_record")
            if latest_record and 'timestamp' in latest_record:
                try:
                    current_ts = datetime.fromisoformat(latest_record['timestamp'].replace('Z', '+00:00'))
                    if overall_latest_timestamp is None or current_ts > overall_latest_timestamp:
                        overall_latest_timestamp = current_ts
                except ValueError:
                    continue # 잘못된 타임스탬프 형식 무시

    if overall_latest_timestamp:
        # 마지막 기록 시간 UTC ISO 문자열로 표시
        print(f"🔄 마지막 기록 시간 ({overall_latest_timestamp.isoformat()}) 이후의 메시지만 스캔합니다.")
    else:
        print("🔄 저장된 기록이 없습니다. 전체 채널 히스토리를 스캔합니다 (시간이 걸릴 수 있습니다)...")

    history_processed_count = 0

    for channel_id, channel_name in TARGET_CHANNEL_IDS.items():
        channel_id_str = str(channel_id)
        print(f"  [{channel_name}] 채널 기록 조회 중... ({'전체' if overall_latest_timestamp is None else '누락분만'})")

        try:
            channel = await bot.fetch_channel(channel_id)
            # after 파라미터 사용: overall_latest_timestamp 이후의 메시지만 가져옴 (오래된 순 -> 최신 순)
            # overall_latest_timestamp가 None이면 전체 기록 조회
            async for message in channel.history(limit=None, after=overall_latest_timestamp, oldest_first=True):
                message_count = 0 # 루프 내에서 카운트하는 것은 비효율적이므로 제거
                # if message_count % 5000 == 0: # 진행 상황 표시는 전체 스캔 시에만 의미있음
                #     print(f"    [{channel_name}] {message_count}개 메시지 처리 중...")

                # process_heartbeat_message가 사용자 파일 저장 및 메모리 업데이트 처리
                await process_heartbeat_message(message, channel_id_str, channel_name)
                history_processed_count += 1 # 실제로 처리된 메시지 수 카운트

            # 채널별 메시지 처리 완료 로그 추가
            print(f"    [{channel_name}] 스캔 완료.")

        except discord.NotFound:
            print(f"❌ 채널을 찾을 수 없음: {channel_name} ({channel_id})")
        except discord.Forbidden:
            print(f"❌ 채널 접근 권한 없음: {channel_name} ({channel_id})")
        except Exception as e:
            print(f"❌ [{channel_name}] 히스토리 조회 중 오류 발생: {e}")

    print(f"✅ 채널 히스토리 스캔 완료 ({history_processed_count}개 처리됨). 메모리에 최신 상태 로드됨.")
    print(f'👂 감시 채널: {list(TARGET_CHANNEL_IDS.values())}')

@bot.event
async def on_message(message):
    """메시지 수신 시 실행되는 이벤트 핸들러 (실시간 처리)"""
    # 봇 자신의 메시지는 무시
    if message.author == bot.user:
        return

    # 대상 채널의 메시지만 처리
    if message.channel.id in TARGET_CHANNEL_IDS:
        channel_id_str = str(message.channel.id)
        channel_name = TARGET_CHANNEL_IDS[message.channel.id]

        # process_heartbeat_message 내부에서 파일 저장 및 메모리 업데이트 처리
        await process_heartbeat_message(message, channel_id_str, channel_name)

async def check_heartbeat_status():
    """메모리의 최신 heartbeat 기록을 바탕으로 주기적으로 상태를 확인하는 함수"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(60) # 60초마다 확인

        now_utc = datetime.now(timezone.utc)
        offline_threshold = timedelta(minutes=10)

        print("\n--- Heartbeat 상태 확인 (메모리 최신 기록 기준) ---")
        # 채널별로 사용자 그룹화
        channel_status = {cid_str: {"online": [], "offline": []} for cid_str in map(str, TARGET_CHANNEL_IDS.keys())}

        if not heartbeat_records:
             print("  표시할 Heartbeat 데이터가 없습니다.")
             continue # 확인할 데이터 없으면 다음 루프

        # 메모리 레코드 순회
        for user_name, data in heartbeat_records.items():
            latest_record = data.get("latest_record")
            channel_id_str = data.get("channel_id_str")

            if not latest_record or not channel_id_str or channel_id_str not in channel_status:
                print(f"⚠️ 사용자 '{user_name}'의 메모리 데이터 오류 또는 대상 채널 아님. 스킵됨.")
                continue

            try:
                last_seen_iso = latest_record['timestamp']
                last_seen = datetime.fromisoformat(last_seen_iso.replace('Z', '+00:00'))
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)

                if now_utc - last_seen > offline_threshold:
                    channel_status[channel_id_str]["offline"].append(user_name)
                else:
                    channel_status[channel_id_str]["online"].append(user_name)
            except KeyError:
                 # 마지막 확인 시간 표시
                 last_seen_kst = format_kst(last_seen_iso) # 오류 발생 전 iso 값 사용 시도
                 print(f"⚠️ 사용자 '{user_name}'의 최신 기록에 timestamp 필드 없음. Offline 처리.")
                 channel_status[channel_id_str]["offline"].append(f"{user_name}(오류)")
            except ValueError:
                 # UTC ISO 문자열 그대로 표시
                 print(f"⚠️ 사용자 '{user_name}'의 시간 형식 오류: {last_seen_iso}. Offline 처리.")
                 channel_status[channel_id_str]["offline"].append(f"{user_name}(오류)")

        # 결과 출력 (채널별)
        for channel_id_str, status in channel_status.items():
            try:
                channel_name = TARGET_CHANNEL_IDS.get(int(channel_id_str), f"Unknown Channel ({channel_id_str})")
                print(f"[{channel_name}]")
                online_users = status["online"]
                offline_users = status["offline"]
                print(f"  Online ({len(online_users)}명): {', '.join(sorted(online_users)) if online_users else '없음'}")
                if offline_users:
                    print(f"  Offline ({len(offline_users)}명): {', '.join(sorted(offline_users))}")
            except ValueError:
                print(f"- 잘못된 채널 ID 형식 무시: {channel_id_str}")

        print("----------------------------------------------\n")

        # 주기적으로 최근 데이터 정리는 더 이상 필요 없음

async def main():
    """메인 실행 함수"""
    async with bot:
        # check_heartbeat_status 태스크 시작 (데이터 정리 포함)
        bot.loop.create_task(check_heartbeat_status())
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
