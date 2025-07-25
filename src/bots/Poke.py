import discord
import asyncio
import requests
import time
import json
import re
import math
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import logging
from pathlib import Path
import sys

# .env 파일 먼저 로드 (PROJECT_ROOT 환경변수를 사용하기 위해)
load_dotenv()

# PROJECT_ROOT를 sys.path에 추가
project_root = os.getenv('PROJECT_ROOT')
if project_root:
    sys.path.insert(0, project_root)

# 프로젝트 모듈 import (절대 경로)
from src.modules import GISTAdapter as GIST  # LocalFile을 사용하는 어댑터
from src.modules.paths import ensure_directories, LOGS_DIR
from src.modules.PokeConfig import get_time_thresholds, get_bad_thresholds, get_special_conditions

# 로깅 설정 함수
def setup_logging():
    """로깅 설정"""
    # 로그 디렉토리 생성 (paths.py의 LOGS_DIR 사용)
    log_dir = Path(LOGS_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # 로그 파일명
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"poke_log_{timestamp}.log"
    
    # 로거 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

# 로거 초기화
logger = setup_logging()

# TEST_MODE 확인
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
if TEST_MODE:
    logger.info("[TEST MODE] Using test configuration")
else:
    logger.info("[PRODUCTION MODE] Using production configuration")

MAIN_CHANNEL = os.getenv('DISCORD_MAIN_CHANNEL_ID')

# 멤버 관련 설정
ID   = os.getenv('GIST_ID_1')
NAME = "Alliance"
Member = GIST.JSON(ID, NAME)

ID   = os.getenv('GIST_ID_1')
NAME = "Admin"
Admin = GIST.TEXT(ID, NAME)

# 서버 설정 공간
SERVER_DICT = {}

if TEST_MODE:
    # TEST MODE: TEST 그룹 하나만 사용
    ID   = os.getenv('GIST_ID_2')
    NAME = "GroupTest"
    GroupTest = GIST.TEXT(ID, NAME, False)
    
    ID   = os.getenv('GIST_ID_3')
    NAME = "GodPackTest"
    GodPackTest = GIST.JSON(ID, NAME)
    
    ID   = os.getenv('GIST_ID_3')
    NAME = "CodeTest"
    CodeTest = GIST.JSON(ID, NAME)
    
    ID      = int(os.getenv('DISCORD_TEST_HEARTBEAT_ID'))
    DETECT  = int(os.getenv('DISCORD_TEST_DETECT_ID'))
    POSTING = int(os.getenv('DISCORD_TEST_POSTING_ID'))
    COMMAND = int(os.getenv('DISCORD_TEST_COMMAND_ID'))
    MUSEUM  = int(os.getenv('DISCORD_TEST_MUSEUM_ID'))
    TAG = {
            "Yet"    : int(os.getenv('DISCORD_TEST_TAG_YET')),
            "Good"   : int(os.getenv('DISCORD_TEST_TAG_GOOD')),
            "Bad"    : int(os.getenv('DISCORD_TEST_TAG_BAD')),
            "1P"     : int(os.getenv('DISCORD_TEST_TAG_1P')),
            "2P"     : int(os.getenv('DISCORD_TEST_TAG_2P')),
            "3P"     : int(os.getenv('DISCORD_TEST_TAG_3P')),
            "4P"     : int(os.getenv('DISCORD_TEST_TAG_4P')),
            "5P"     : int(os.getenv('DISCORD_TEST_TAG_5P')),
            "Notice" : int(os.getenv('DISCORD_TEST_TAG_NOTICE'))
    }
    
    SERVER_DICT[ID] = GIST.SERVER(ID, GroupTest, GodPackTest, CodeTest, DETECT, POSTING, COMMAND, MUSEUM, TAG)
    
else:
    # PRODUCTION MODE: GROUP7과 GROUP8 사용
    ID   = os.getenv('GIST_ID_2')
    NAME = "Group7"
    Group7 = GIST.TEXT(ID, NAME, False)
    
    ID   = os.getenv('GIST_ID_3')
    NAME = "GodPack7"
    GodPack7 = GIST.JSON(ID, NAME)
    
    ID   = os.getenv('GIST_ID_3')
    NAME = "Code7"
    GPTest7 = GIST.JSON(ID, NAME)
    
    ID      = int(os.getenv('DISCORD_GROUP7_HEARTBEAT_ID'))
    DETECT  = int(os.getenv('DISCORD_GROUP7_DETECT_ID'))
    POSTING = int(os.getenv('DISCORD_GROUP7_POSTING_ID'))
    COMMAND = int(os.getenv('DISCORD_GROUP7_COMMAND_ID'))
    MUSEUM  = int(os.getenv('DISCORD_GROUP7_MUSEUM_ID'))
    TAG = {
            "Yet"    : int(os.getenv('DISCORD_GROUP7_TAG_YET')),
            "Good"   : int(os.getenv('DISCORD_GROUP7_TAG_GOOD')),
            "Bad"    : int(os.getenv('DISCORD_GROUP7_TAG_BAD')),
            "1P"     : int(os.getenv('DISCORD_GROUP7_TAG_1P')),
            "2P"     : int(os.getenv('DISCORD_GROUP7_TAG_2P')),
            "3P"     : int(os.getenv('DISCORD_GROUP7_TAG_3P')),
            "4P"     : int(os.getenv('DISCORD_GROUP7_TAG_4P')),
            "5P"     : int(os.getenv('DISCORD_GROUP7_TAG_5P')),
            "Notice" : int(os.getenv('DISCORD_GROUP7_TAG_NOTICE'))
    }
    
    SERVER_DICT[ID] = GIST.SERVER(ID, Group7, GodPack7, GPTest7, DETECT, POSTING, COMMAND, MUSEUM, TAG)
    
    ID   = os.getenv('GIST_ID_2')
    NAME = "Group8"
    Group8 = GIST.TEXT(ID, NAME, False)
    
    ID   = os.getenv('GIST_ID_3')
    NAME = "GodPack8"
    GodPack8 = GIST.JSON(ID, NAME)
    
    ID   = os.getenv('GIST_ID_3')
    NAME = "Code8"
    GPTest8 = GIST.JSON(ID, NAME)
    
    ID      = int(os.getenv('DISCORD_GROUP8_HEARTBEAT_ID'))
    DETECT  = int(os.getenv('DISCORD_GROUP8_DETECT_ID'))
    POSTING = int(os.getenv('DISCORD_GROUP8_POSTING_ID'))
    COMMAND = int(os.getenv('DISCORD_GROUP8_COMMAND_ID'))
    MUSEUM  = int(os.getenv('DISCORD_GROUP8_MUSEUM_ID'))
    TAG = {
            "Yet"    : int(os.getenv('DISCORD_GROUP8_TAG_YET')),
            "Good"   : int(os.getenv('DISCORD_GROUP8_TAG_GOOD')),
            "Bad"    : int(os.getenv('DISCORD_GROUP8_TAG_BAD')),
            "1P"     : int(os.getenv('DISCORD_GROUP8_TAG_1P')),
            "2P"     : int(os.getenv('DISCORD_GROUP8_TAG_2P')),
            "3P"     : int(os.getenv('DISCORD_GROUP8_TAG_3P')),
            "4P"     : int(os.getenv('DISCORD_GROUP8_TAG_4P')),
            "5P"     : int(os.getenv('DISCORD_GROUP8_TAG_5P')),
            "Notice" : int(os.getenv('DISCORD_GROUP8_TAG_NOTICE'))
    }
    SERVER_DICT[ID] = GIST.SERVER(ID, Group8, GodPack8, GPTest8, DETECT, POSTING, COMMAND, MUSEUM, TAG)
#  봇 권한 설정
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)


USER_DICT = {}
for name, code in Member.DATA.items():
    USER_DICT[name] = GIST.USER(name, code)

@bot.event
async def on_ready():
    """봇이 Discord에 연결되었을 때 실행"""
    logger.info(f'[BOT READY] {bot.user} has connected to Discord!')
    logger.info(f'[BOT READY] Connected to {len(bot.guilds)} guild(s)')
    
    is_test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    if is_test_mode:
        logger.info(f'[TEST MODE] Running in test environment')
        logger.info(f'[TEST MODE] Monitoring channels:')
        for server_id, server in SERVER_DICT.items():
            logger.info(f'  - {server.FILE.NAME}: HEARTBEAT={server.ID}, COMMAND={server.COMMAND}')
    
    
async def safe_send(channel, message, BLOCK=False):
    MAX_LENGTH = 1800

    if len(message) <= MAX_LENGTH:
        if BLOCK:
            message = f"```\n{message}\n```"
        await channel.send(message)
        return

    lines = message.split('\n')
    chunk = ""

    for line in lines:
        overhead = 8 if BLOCK else 0
        if len(chunk) + len(line) + 1 + overhead <= MAX_LENGTH:
            chunk += line + '\n'
        else:
            if BLOCK:
                await channel.send(f"```\n{chunk.strip()}\n```")
            else:
                await channel.send(chunk.strip())
            chunk = line + '\n'

    if chunk.strip():
        if BLOCK:
            await channel.send(f"```\n{chunk.strip()}\n```")
        else:
            await channel.send(chunk.strip())

async def safe_history(thread, retries=5):
    for attempt in range(retries):
        try:
            return [msg async for msg in thread.history(limit=50)]
        except Exception as e:
            logger.warning(f"⚠️ 메시지 가져오기 실패 (시도 {attempt + 1}/{retries}): {e}")
            await asyncio.sleep(2 ** attempt)
    logger.error(f"⛔ 최종 실패: {thread.name}")
    return None

def is_my_channel(channel_id):
    """현재 봇이 관리하는 채널인지 확인"""
    for server_id, server in SERVER_DICT.items():
        # Heartbeat ID를 키로 사용하는 서버인 경우
        if server_id == channel_id:
            return True
        # 서버가 관리하는 채널들 체크
        if hasattr(server, 'DETECT') and channel_id == server.DETECT:
            return True
        if hasattr(server, 'POSTING') and channel_id == server.POSTING:
            return True
        if hasattr(server, 'COMMAND') and channel_id == server.COMMAND:
            return True
        if hasattr(server, 'MUSEUM') and channel_id == server.MUSEUM:
            return True
    return False

async def safe_fetch_channel(channel, retries=5):
    for attempt in range(retries):
        try:
            return bot.fetch_channel(channel)
        except Exception as e:
            logger.warning(f"⚠️ 채널 가져오기 실패 (시도 {attempt + 1}/{retries}): {e}")
            await asyncio.sleep(2 ** attempt)
    logger.error(f"⛔ 최종 실패: {channel}")
    return None

async def recent_godpack(Server):
    now = datetime.now(timezone.utc)
    day = 4
    days_ago = now - timedelta(hours=24*day)
    
    logger.info(f"채널 ID: {Server.DETECT}에서 {day}일 이내 메시지 조회 시작")
    channel = await bot.fetch_channel(Server.DETECT)
    try:
        messages = [msg async for msg in channel.history(limit=1000)]
        logger.info(f"총 {len(messages)}개의 메시지를 확인했습니다.")

        detected_gp = 0
        for message in messages:
            if message.created_at >= days_ago:
                if "Invalid" in message.content :
                    continue
                if "found by" in message.content :
                    lines = message.content.split("\n")
                    if len(lines) > 2:
                        inform = Server.extract_Pseudo(lines)
                        if inform :
                            detected_gp += 1
                            message_time_utc = message.created_at
                            message_time_kst = message_time_utc + timedelta(hours=9)
                            formatted_time = message_time_kst.strftime("%Y.%m.%d %H:%M")
                            title, sub, save = Server.make_title(inform, formatted_time)
                            
                            if save not in Server.GODPACK.DATA :
                                Server.GODPACK.edit('+', save, "Yet")
                                if inform['code'] :
                                    Server.GPTEST.edit('+', save, inform['code'])
                                else :
                                    Server.GPTEST.edit('+', save, 'NaN')
                if "Valid" in message.content :
                    lines = message.content.split("\n")
                    if len(lines) > 3:
                        inform = Server.extract_GodPack(lines)
                        if inform :
                            detected_gp += 1
                            message_time_utc = message.created_at
                            message_time_kst = message_time_utc + timedelta(hours=9)
                            formatted_time = message_time_kst.strftime("%Y.%m.%d %H:%M")
                            title, sub, save = Server.make_title(inform, formatted_time)
                            
                            if save not in Server.GODPACK.DATA :
                                Server.GODPACK.edit('+', save, "Yet")
                                if inform['code'] :
                                    Server.GPTEST.edit('+', save, inform['code'])
                                else :
                                    Server.GPTEST.edit('+', save, 'NaN')

        logger.info(f"최근 {day}일 이내 감지된 레어팩 수: {detected_gp}개")
        Server.GODPACK.update()
        Server.GPTEST.update()
        
    except Exception as e:
        logger.error(f"❌ 메시지 불러오는 중 오류 발생: {e}")


async def recent_online(Server):
    now = datetime.now(timezone.utc)
    
    # TEST_MODE일 때는 10초 타임아웃 사용
    if TEST_MODE:
        Threshold = {'Off' : now - timedelta(seconds=10),
                     'Rest': now - timedelta(hours=24*7)}
    else:
        Threshold = {'Off' : now - timedelta(minutes=15),
                     'Rest': now - timedelta(hours=24*7)}

    channel = await bot.fetch_channel(Server.ID)
    
    logger.info(f"채널 ID: {Server.ID}에서 최근 메시지 조회 시작")
    try:
        messages = [msg async for msg in channel.history(limit=500)]
        logger.info(f"총 {len(messages)}개의 메시지를 확인했습니다.")
        for message in messages:
            if "Online:" in message.content:
                if message.created_at >= Threshold["Off"]:
                    
                    name = message.content.split("\n")[0].strip()
                    if name in USER_DICT.keys():
                        if USER_DICT[name].CODE not in Server.FILE.DATA:
                            USER_DICT[name].called(Server, message)
                            USER_DICT[name].onlined(Server)
                    else :
                        await channel.send(f"{name} 은 ID 목록에 없습니다.")
                        
                elif message.created_at >= Threshold["Rest"] :
                    name = message.content.split("\n")[0].strip()
                    if name in USER_DICT.keys():
                        if USER_DICT[name].CODE not in Server.FILE.DATA and USER_DICT[name].off.get(Server.ID, None) is None:
                            USER_DICT[name].offlined(Server, message)

        logger.info(f"✅ 최근 15분 이내에 감지된 온라인 유저 수: {len(Server.FILE.DATA)}명")
        Server.FILE.update()
        
    except Exception as e:
        logger.error(f"❌ 메시지 불러오는 중 오류 발생: {e}")

async def recent_offline(Server):
    now = datetime.now(timezone.utc)
    
    # TEST_MODE일 때는 10초 타임아웃 사용
    if TEST_MODE:
        Threshold = {'Off' : now - timedelta(seconds=10),
                     'Rest': now - timedelta(hours=24*7)}
    else:
        Threshold = {'Off' : now - timedelta(minutes=15),
                     'Rest': now - timedelta(hours=24*7)}

    channel = await bot.fetch_channel(Server.ID)
    
    logger.info(f"채널 ID: {Server.ID}에서 오래된 메시지 조회 시작")
    try:
        messages_old = [msg async for msg in channel.history(limit=50000)]
        logger.info(f"총 {len(messages_old)}개의 메시지를 확인했습니다.")
        for message in messages_old :
            if "Online:" in message.content:
                if message.created_at < Threshold["Off"] and message.created_at >= Threshold["Rest"] :
                    name = message.content.split("\n")[0].strip()
                    if name in USER_DICT.keys():
                        if USER_DICT[name].CODE not in Server.FILE.DATA and USER_DICT[name].off.get(Server.ID, None) is None:
                            USER_DICT[name].offlined(Server, message)
                            
        logger.info("오프라인 유저를 모두 확인했습니다.")
    except Exception as e:
        logger.error(f"❌ 메시지 불러오는 중 오류 발생: {e}")
        
        
async def do_update():
    """온라인 상태 업데이트 수행 (테스트 명령어와 주기적 실행 공통)"""
    logger.info(f"[PERIODIC] do_update 실행 - {datetime.now().strftime('%H:%M:%S')}")
    Server_Channel = {ID : await bot.fetch_channel(ID) for ID, Server in SERVER_DICT.items()}
    
    # 타임아웃 체크 추가
    now = datetime.now(timezone.utc)
    timeout = timedelta(seconds=10) if TEST_MODE else timedelta(minutes=15)
    
    for ID, Server in SERVER_DICT.items():
        # 타임아웃된 사용자 확인
        remove = [user for user in Server.ONLINE if now - user.inform[Server.ID]['TIME'] >= timeout]
        
        if remove:
            for user in remove:
                user.offline(Server)
                logger.info(f"[TIMEOUT] {user.NAME} 님이 OFF-LINE 되었습니다.")
                Server.FILE.update()
                await Server_Channel[ID].send(f"{user.NAME} 님이 OFF-LINE 되었습니다.")
    
    # 기존 WAITING → ONLINE 처리
    RAW_GIST_DICT = {}
    for ID, Server in SERVER_DICT.items() :
        RAW_GIST_DICT[ID] = Server.FILE.fetch_raw()
        for user in list(Server.WAITING) :
            if user.CODE in RAW_GIST_DICT[ID] :
                Server.WAITING.discard(user)
                Server.ONLINE.add(user)
                logger.info(f"{user.NAME} 님이 GIST에 업데이트 되었습니다!")
                await Server_Channel[ID].send(f"{user.NAME} 님이 GIST에 업데이트 되었습니다!")
            else :
                logger.debug(f"{user.NAME} 님의 GIST 업데이트 대기 중...")
                await Server_Channel[ID].send(f"{user.NAME} 님의 GIST 업데이트 대기 중...")

async def update_periodic():
    """주기적으로 update 실행"""
    # TEST_MODE일 때는 5초, 일반 모드는 30초
    sleep_time = 5 if TEST_MODE else 30
    logger.info(f"update_periodic 시작 {sleep_time}초 주기로 실행")
    while True:
        await asyncio.sleep(sleep_time)
        await do_update()


async def do_verify(Server):
    """갓팩 검증 수행 (테스트 명령어와 주기적 실행 공통)"""
    Server.Health = datetime.now(timezone.utc) + timedelta(hours=9)
    
    # 서버별 시간 설정 가져오기
    times = get_time_thresholds(Server.FILE.NAME)
    bad_threshold = get_bad_thresholds(Server.FILE.NAME)
    special_conditions = get_special_conditions(Server.FILE.NAME)
    
    forum_channel = await bot.fetch_channel(Server.POSTING)
    alert_channel = await bot.fetch_channel(Server.DETECT)
    main_channel  = await bot.fetch_channel(MAIN_CHANNEL)
    
    threads = forum_channel.threads

    forum_tags = forum_channel.available_tags

    async for thread in forum_channel.archived_threads(limit=100):
        try:
            if thread.archived:
                await thread.edit(archived=False)
                await asyncio.sleep(1)
            threads.append(thread)
        except Exception as e:
            logger.error(f"❌ 스레드 {thread.name} 복원 중 오류 발생: {e}")
    
        
    for thread in threads.copy() :
        thread_tags_ids = [tag.id for tag in thread.applied_tags]
        
        if Server.Tag["Bad"] in thread_tags_ids :
            try :
                parts = thread.name.split()
                KST = timezone(timedelta(hours=9))
                time_str = f"{parts[7]} {parts[8]}"
                thread_created_at = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=KST)
            except :
                thread_created_at = thread.created_at
                
            if thread_created_at < times["bad_delete_threshold"] :
                try :
                    logger.info(f"{thread.name}이 삭제 됩니다.")
                    await thread.delete()
                    await asyncio.sleep(2)
                    threads.remove(thread)
                except Exception as e:
                    logger.error(f"{thread.name} 삭제에 실패했습니다", e)
                    
        

    THREAD_DICT = {"Yet":[], "Bad":[], "Good":[], "Notice":[], "Error":[]}
    
    for thread in threads :
            thread_name = thread.name
            thread_tags = thread.applied_tags
            
            thread_tags_ids = [tag.id for tag in thread_tags]
            
            if Server.Tag["Notice"] in thread_tags_ids :
                THREAD_DICT["Notice"].append(thread)
                
            elif Server.Tag["Yet"] in thread_tags_ids :
                # 설정에서 가져온 값 사용
                now = times["now"]
                one_ago = times["one_ago"]
                time_threshold = times["time_threshold"]
                
                messages = await safe_history(thread)
                if messages is None:
                    THREAD_DICT["Error"].append(thread)
                    continue
                
                bad  = 0
                good = 0
                no   = 0
                for reply in messages :
                    if "👍" in reply.content :
                        good += 1
                    elif "👎" in reply.content :
                        bad += 1
                    elif "❓" in reply.content :
                        no += 1
                try :
                    parts = thread.name.split()
                    KST = timezone(timedelta(hours=9))
                    time_str = f"{parts[7]} {parts[8]}"
                    thread_created_at = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=KST)
                except :
                    thread_created_at = thread.created_at
                    
                if good >= 1 :
                    tag_id = Server.Tag["Good"]
                    good_tag = next((tag for tag in forum_tags if tag.id == tag_id), None)
                    THREAD_DICT["Good"].append(thread)
                    await thread.edit(applied_tags = [good_tag])
                else :
                    title_divide = thread.name.split()
                    pack = title_divide[5]
                    
                    if no + bad + good == 0 :
                        if thread_created_at < one_ago :
                            tag_id = Server.Tag["Bad"]
                            bad_tag = next((tag for tag in forum_tags if tag.id == tag_id), None)
                            THREAD_DICT["Bad"].append(thread)
                            await thread.edit(applied_tags = [bad_tag])
                        else :
                            THREAD_DICT["Yet"].append(thread)
                    
                    elif no >= special_conditions["min_question_count"] and bad == 0 :
                        if thread_created_at < one_ago :
                            tag_id = Server.Tag["Bad"]
                            bad_tag = next((tag for tag in forum_tags if tag.id == tag_id), None)
                            THREAD_DICT["Bad"].append(thread)
                            await thread.edit(applied_tags = [bad_tag])
                        else :
                            THREAD_DICT["Yet"].append(thread)
                        
                    
                    elif pack in ["2P", "3P", "4P", "5P"] :
                        if thread_created_at < time_threshold.get(pack, time_threshold["1P"]) or bad >= bad_threshold.get(pack, 99) :
                            tag_id = Server.Tag["Bad"]
                            bad_tag = next((tag for tag in forum_tags if tag.id == tag_id), None)
                            THREAD_DICT["Bad"].append(thread)
                            await thread.edit(applied_tags = [bad_tag])
                        else :
                            THREAD_DICT["Yet"].append(thread)
                    
                    elif pack == "1P" :
                        if thread_created_at < time_threshold.get(pack, time_threshold["1P"]) :
                            tag_id = Server.Tag["Bad"]
                            bad_tag = next((tag for tag in forum_tags if tag.id == tag_id), None)
                            THREAD_DICT["Bad"].append(thread)
                            await thread.edit(applied_tags = [bad_tag])
                        else :
                            THREAD_DICT["Yet"].append(thread)
            
                    else :
                        logger.warning(f"유효하지 않은 포스트가 검증 채널에 있습니다.\n제목 : {thread_name}")
                        await alert_channel.send(f"유효하지 않은 포스트가 검증 채널에 있습니다.\n제목 : {thread_name}")
                    
            elif Server.Tag["Bad"] in thread_tags_ids :
                THREAD_DICT["Bad"].append(thread)

            elif Server.Tag["Good"] in thread_tags_ids :
                THREAD_DICT["Good"].append(thread)
                    
            else :
                logger.warning(f"유효하지 않은 포스트가 검증 채널에 있습니다.\n제목 : {thread_name}")
                await alert_channel.send(f"유효하지 않은 포스트가 검증 채널에 있습니다.\n제목 : {thread_name}")

        
    yet_list = [text for text, verify in Server.GODPACK.DATA.items() if verify == 'Yet']
    yet_change = False
    for text in yet_list :
        parts = text.split()
        title = f"{parts[2]} {parts[3]} / {parts[4]} / {parts[5]} / {parts[0]} {parts[1]}"
        if title in [temp.name for temp in THREAD_DICT["Yet"]] :
            continue
        else :
            if title in [temp.name for temp in THREAD_DICT["Good"]] :
                thread = next((temp for temp in THREAD_DICT["Good"] if title == temp.name), None)
                Server.GODPACK.edit('+', text, "Good")
                yet_change = True
                logger.info(f"❗❗ {parts[2]} {parts[3]} 은 축으로 검증 되었습니다.")
                await alert_channel.send(f"🎉 {parts[2]} {parts[3]} 은 축으로 검증 되었습니다.")
                await main_channel.send(f"🎉 {parts[2]} {parts[3]} 은 축으로 검증 되었습니다. ({Server.FILE.NAME})")
                try:
                    museum_channel = await bot.fetch_channel(Server.MUSEUM)
                    await Server.post_museum(thread, museum_channel)
                except Exception as e:
                    logger.error(f"{title} 박물관 전시 실패! ", e)
            
            elif title in [temp.name for temp in THREAD_DICT["Bad"]] :
                Server.GODPACK.edit('+', text, "Bad")
                Server.GPTEST.edit('-', text, None)
                yet_change = True
                logger.info(f"❗❗ {parts[2]} {parts[3]} 은 망으로 검증 되었습니다.")
                await alert_channel.send(f"❗❗ {parts[2]} {parts[3]} 은 망으로 검증 되었습니다.")
            elif title in [temp.name for temp in THREAD_DICT["Error"]] :
                logger.error(f"❗❗ {parts[2]} {parts[3]} 에 오류가 있습니다.")
            else :
                KST = timezone(timedelta(hours=9))
                timenow = datetime.now(KST)

                time_str = f"{parts[0]} {parts[1]}"
                parsed_time = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=KST)
                
                if abs(timenow - parsed_time) <= timedelta(minutes=10) :
                    continue
                    
                    logger.warning(f"⚠️{title} 포스트를 찾을 수 없습니다.")
                    await alert_channel.send(f"{title} 포스트를 찾을 수 없어 임시로 생성합니다.")
                    
                    inform = {"name" : parts[2], "number" : parts[3], "pack" : parts[5][:-1], "percent" : parts[4][:-1]}
                    try:
                        now = datetime.now(timezone.utc)
                        days_ago = now - timedelta(hours=24*4)
                        messages = [msg async for msg in alert_channel.history(limit=1000)]
                        
                        images = False
                        for message in messages:
                            if message.created_at >= days_ago:
                                if "Invalid" in message.content :
                                    continue
                                if "found by" in message.content or "Valid" in message.content or "God" in message.content:
                                    lines = message.content.split("\n")
                                    for line in lines :
                                        if parts[2] + parts[3] in line :
                                            images = message.attachments
                                            break
                                        
                    except Exception as e:
                        logger.error(f"❌ 메시지 불러오는 중 오류 발생: {e}")
                    try:
                        await Server.Post(forum_channel, images, inform, title)
                    except Exception as e:
                        logger.error(f"{title} 포스팅 실패 : ", e)
                    await asyncio.sleep(1)
        if yet_change :
            Server.GODPACK.update()
            Server.GPTEST.update()

async def verify_periodic(Server):
    """주기적으로 verify 실행"""
    while True:
        await asyncio.sleep(120)
        await do_verify(Server)

@bot.event
async def on_ready():
    logger.info(f"✅ 로그인됨: {bot.user}")
    
    for server in SERVER_DICT.values():
        await recent_online(server)
    for server in SERVER_DICT.values():
        await recent_godpack(server)
        await asyncio.sleep(30)
    for server in SERVER_DICT.values():
        await recent_offline(server)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # 내가 관리하는 채널이 아니면 무시
    if not is_my_channel(message.channel.id):
        return
    
    await bot.process_commands(message)
    
    if message.channel.id in SERVER_DICT:
        if "Online:" in message.content:
            Server = SERVER_DICT[message.channel.id]
            name = message.content.split("\n")[0].strip()
            if name in USER_DICT.keys():
                USER_DICT[name].called(Server, message)
                if USER_DICT[name].CODE not in Server.FILE.DATA:
                    logger.info(f"✅ 수집된 이름: {name}, 코드 : {USER_DICT[name].CODE}")
                    USER_DICT[name].online(Server)
                    Server.FILE.update()
                    await message.channel.send(f"로그인 시도 : {name}")
                    await message.channel.send("GIST 업데이트까지 약 5분 정도 소요됩니다.")
                
            else :
                await message.channel.send(f"{name} 은 ID 목록에 없습니다.")
    
    
    if message.channel.id in [Server.DETECT for Server in SERVER_DICT.values()] :
        for Server in SERVER_DICT.values():
            if message.channel.id == Server.DETECT:
                break
        
        if "Invalid" in message.content:
            logger.debug("Invalid God Pack 을 찾았습니다.")
            return
        
        elif "found by" in message.content:
            logger.info("Pseudo God Pack 을 찾았습니다.")
            inform, title = Server.found_Pseudo(message)
            
            if inform and title :
                images = message.attachments
                forum_channel = bot.get_channel(Server.POSTING)
                await Server.Post(forum_channel, images, inform, title)
            else :
                logger.warning("메시지에 오류가 있었습니다")

        
        elif "Valid" in message.content :
            logger.info("God Pack 을 찾았습니다!")
            inform, title = Server.found_GodPack(message)
            
            if inform and title :
                images = message.attachments
                forum_channel = bot.get_channel(Server.POSTING)
                await Server.Post(forum_channel, images, inform, title)
            else :
                logger.warning("메시지에 오류가 있었습니다")
                
def yet_str(text, add = None) :
    parts = text.split()
    nameber = parts[2]+' '+parts[3]
    if add :
        nameber = nameber+' '+add
    return f"{nameber:<15} | {parts[0]:<5} {parts[1]:<5} | {parts[4]:<4} {parts[5]}"

def convert_str(text) :
    parts = text.split()
    nameber = parts[2]+' '+parts[3]
    return f"{parts[0]:<5} {parts[1]:<5} | {nameber:<15} | {parts[4]:<4} {parts[5]}"

def Is_recent(date_str, time_str, ago):
    now = datetime.now()
    days_ago = now - timedelta(days=ago)
    date_obj = datetime.strptime(f"{date_str} {time_str}", "%Y.%m.%d %H:%M")
    return date_obj >= days_ago

async def change_pack(ctx, name, number, Mode) :
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에 해주세요.")
        return
    
    nameber = name + ' ' + number
    
    godpacks = [text for text in Server.GODPACK.DATA if nameber in text]
    
    alert_channel = await bot.fetch_channel(Server.DETECT)
    main_channel  = await bot.fetch_channel(MAIN_CHANNEL)
    
    if len(godpacks) > 1:
        text = "\n".join(godpacks)
        await ctx.send("중복 닉네임이 존재합니다.\n변경하실 God Pack의 Index를 말씀해주세요 (1, 2, ...)")
        await ctx.send(f"```{text}```")
        
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
        
        try:
            response = await bot.wait_for("message", check=check, timeout=30.0)  # 30초 동안 대기
            await ctx.send(f"인식한 답변 : {response.content}")
        
            index = int(response.content) - 1
            if index in range(len(godpacks)) :
                if Mode == 'Bad' :
                    await ctx.send(f"{godpacks[index]} 은 망팩 상태가 됩니다.")
                    await alert_channel.send(f"❗❗ {name} {number} 은 망으로 검증 되었습니다.")
                elif Mode == 'Good' :
                    await ctx.send(f"{godpacks[index]} 은 축팩 상태가 됩니다.")
                    await alert_channel.send(f"🎉 {name} {number} 은 축으로 검증 되었습니다.")
                    await main_channel.send(f"🎉 {name} {number} 은 축으로 검증 되었습니다. ({Server.FILE.NAME})")
                elif Mode == 'Yet' :
                    await ctx.send(f"{godpacks[index]} 은 미검증 상태가 됩니다.")
                else :
                    await ctx.send(f"{godpacks[index]} 가 제거되었습니다.")
                
                Server.GODPACK.edit('+', godpacks[index], Mode)
                Server.GODPACK.update()
            else :
                await ctx.send("해당 Index는 없습니다.")
        except asyncio.TimeoutError:
            await ctx.send("응답 시간이 초과 되었습니다. (30초)")
            
    elif len(godpacks) == 1 :
        index = 0
        if Mode == 'Bad' :
            await ctx.send(f"{godpacks[index]} 은 망팩 상태가 됩니다.")
            await alert_channel.send(f"❗❗ {name} {number} 은 망으로 검증 되었습니다.")
        elif Mode == 'Good' :
            await ctx.send(f"{godpacks[index]} 은 축팩 상태가 됩니다.")
            await alert_channel.send(f"🎉 {name} {number} 은 축으로 검증 되었습니다.")
            await main_channel.send(f"🎉 {name} {number} 은 축으로 검증 되었습니다. ({Server.FILE.NAME})")
        elif Mode == 'Yet' :
            await ctx.send(f"{godpacks[index]} 은 미검증 상태가 됩니다.")
        else :
            await ctx.send(f"{godpacks[index]} 가 제거되었습니다.")
        
        Server.GODPACK.edit('+', godpacks[index], Mode)
        Server.GODPACK.update()
    else :
        await ctx.send("해당 God Pack은 없습니다.")


@bot.command()
async def fail(ctx, name, number):    
    await change_pack(ctx, name, number, 'Bad')

@bot.command()
async def success(ctx, name, number):    
    await change_pack(ctx, name, number, 'Good')

@bot.command()
async def unknown(ctx, name, number):    
    await change_pack(ctx, name, number, 'Yet')
    
@bot.command()
async def remove(ctx, name, number):    
    await change_pack(ctx, name, number, 'NaN')
    
@bot.command()
async def yet(ctx):
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에 해주세요.")
        return

    yet_list = [yet_str(text) for text, verify in Server.GODPACK.DATA.items() if verify == 'Yet']
    yet_list = sorted(yet_list, key=lambda s: (s.lower(), s))
    
    recent_good = set()
    for text, verify in Server.GODPACK.DATA.items() :
        if verify == 'Good' :
            parts = text.split()
            date = parts[0]
            hour = parts[1]
            if Is_recent(date, hour, 2) :
                recent_good.add(yet_str(text, "**"))
                
            elif Is_recent(date, hour, 4) :
                recent_good.add(yet_str(text, "*"))
                
                
    recent_good_list = sorted(recent_good)
    
    total_list = yet_list + recent_good_list
    total_list = sorted(total_list, key=lambda s: (s.lower(), s))
    
    if yet_list or recent_good_list:
        total_message = "\n".join(total_list)
        full_message  = f"최근 축팩 및 미검증 리스트 {len(total_list)}\n(** : 2일 미만, * : 4일 미만)\n{total_message}"
        await safe_send(ctx, full_message, True)
    else:
        await ctx.send("축팩 및 미검증이 없습니다.")
        
@bot.command()
async def verify(ctx):
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에 해주세요.")
        return
    
    await ctx.send("검증 채널 확인 중...")
    
    forum_channel = await bot.fetch_channel(Server.POSTING)
    
    threads = forum_channel.threads
    async for thread in forum_channel.archived_threads(limit=100):
        threads.append(thread)
    
    Yet_thread = []
    for thread in threads :
        thread_tags = thread.applied_tags
        
        thread_tags_ids = [tag.id for tag in thread_tags]
        
        if Server.Tag["Yet"] in thread_tags_ids :
            Yet_thread.append(thread)
                
            
    status = {}
    for post in Yet_thread :
        messages = [msg async for msg in post.history(limit=50)]
        bad  = 0
        good = 0
        no   = 0
        for reply in messages :
            if "👍" in reply.content :
                good += 1
            elif "👎" in reply.content :
                bad += 1
            elif "❓" in reply.content :
                no += 1
        status[post.name] = (bad, good, no)
        
    yet_list = []
    for text, verify in Server.GODPACK.DATA.items() :
        if verify == 'Yet' :
            parts = text.split()
            title = f"{parts[2]} {parts[3]} / {parts[4]} / {parts[5]} / {parts[0]} {parts[1]}"
            
            if title in status :
                bad, good, no = status[title]
                add = f"{bad:<3}{no:<3}{good:<3}"
                table = " "*(len(convert_str(text))+5) + 'X  ' + '?  ' + 'V  '
                yet_list.append(convert_str(text) + ' '*5 + add)
            else :
                await ctx.send(f"{title} 이 발견되지 않았습니다. 검증 채널을 확인해주세요")
    yet_list.sort()
    
    if yet_list:
        yet_message = "\n".join(yet_list)
        await ctx.send(f"```미검증 리스트 {len(yet_list)}\n{table}\n{yet_message}```")
    else:
        await ctx.send("축팩 및 미검증이 없습니다.")
        
@bot.command()
async def reply(ctx):
    BOT_ID = [155149108183695360,
              1356552284753891379]
    
    guild = ctx.guild
    Members = {}
    Replys  = {}
    async for member in guild.fetch_members(limit=None):
        if member.id not in BOT_ID :
            Members[member.id] = member.display_name
            Replys[member.id]  = 0
    
    await ctx.send("댓글 취합 중... (오래 걸립니다)")
    try:
        for Server in SERVER_DICT.values() :
            forum_channel = await bot.fetch_channel(Server.POSTING)
            
            threads = forum_channel.threads
    
            async for thread in forum_channel.archived_threads(limit=100):
                threads.append(thread)
            
            Recent_thread = []
            for thread in threads :
                now = datetime.now(timezone.utc)
                days_ago = now - timedelta(hours=96)
                one_day = now - timedelta(hours=24)

                try :
                    parts = thread.name.split()
                    KST = timezone(timedelta(hours=9))
                    time_str = f"{parts[7]} {parts[8]}"
                    thread_created_at = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=KST)
                except :
                    thread_created_at = thread.created_at
                if thread_created_at > days_ago :
                    Recent_thread.append(thread)
                    
            for post in Recent_thread :
                messages = [msg async for msg in post.history(limit=100)]
    
                for emoji in messages :
                    if emoji.created_at >= one_day :
                        if "👍" in emoji.content:
                            if emoji.author.id in Replys :
                                Replys[emoji.author.id] += 1
                        elif "👎" in emoji.content :
                            if emoji.author.id in Replys :
                                Replys[emoji.author.id] += 1
                        
            reply_text = "\n".join([
                f"{Members[key]:<12} : {value:<2}개"
                for key, value in sorted(Replys.items(), key=lambda item: item[1], reverse=True)
            ])
        full_text = f"24 시간 이내 검증 횟수 리스트\n{reply_text}"
        await safe_send(ctx, full_text, True)
    except Exception as e:
        logger.error("에러가 있습니다.", e)

@bot.command()
async def custom(ctx):
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에 해주세요.")
        return
    
    await ctx.send("리스트를 커스텀 하는 중...")
    
    who = ctx.author.id
    
    picked = set()
    
    forum_channel = await bot.fetch_channel(Server.POSTING)
    
    threads = forum_channel.threads
    
    async for thread in forum_channel.archived_threads(limit=100):
        try:
            if thread.archived:
                await thread.edit(archived=False)
                await asyncio.sleep(1)
                
            threads.append(thread)
            
        except Exception as e:
            logger.error(f"❌ 스레드 {thread.name} 복원 중 오류 발생: {e}")

    Recent_thread = []
    for thread in threads :
        now = datetime.now(timezone.utc)
        days_ago = now - timedelta(hours=96)

        try :
            parts = thread.name.split()
            KST = timezone(timedelta(hours=9))
            time_str = f"{parts[7]} {parts[8]}"
            thread_created_at = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=KST)
        except :
            thread_created_at = thread.created_at
        
        if thread_created_at > days_ago :
            Recent_thread.append(thread)
    
    Yet_thread  = []
    Good_thread = []
    for thread in Recent_thread : 
        thread_tags = thread.applied_tags
        
        thread_tags_ids = [tag.id for tag in thread_tags]
        
        if Server.Tag["Yet"] in thread_tags_ids :
            Yet_thread.append(thread)
            
        elif Server.Tag["Good"] in thread_tags_ids :
            Good_thread.append(thread)
    
    for post in Yet_thread :
        first_msg = await post.fetch_message(post.id)
        
        for reaction in first_msg.reactions :
            if str(reaction.emoji) in ["👎"] :
                users = set()
                async for user in reaction.users():
                    users.add(user.id)

                if who in users :
                    picked.add(post.name)
                    break
    
    for post in Good_thread :
        first_msg = await post.fetch_message(post.id)
        
        for reaction in first_msg.reactions :
            if str(reaction.emoji) in ["👎"] :
                users = set()
                async for user in reaction.users():
                    users.add(user.id)

                if who in users :
                    picked.add(post.name)
                    break
                
                
    yet_dict = {}
    for text, verify in Server.GODPACK.DATA.items() :
        if verify == 'Yet' :
            parts = text.split()
            title = f"{parts[2]} {parts[3]} / {parts[4]} / {parts[5]} / {parts[0]} {parts[1]}"
            if title in picked :
                continue
            
            yet_dict[text] = verify


    yet_list = [yet_str(text) for text, verify in yet_dict.items()]
    yet_list = sorted(yet_list, key=lambda s: (s.lower(), s))
    
    recent_good = set()
    for text, verify in Server.GODPACK.DATA.items() :
        if verify == 'Good' :
            parts = text.split()
            title = f"{parts[2]} {parts[3]} / {parts[4]} / {parts[5]} / {parts[0]} {parts[1]}"
            
            if title in picked :
                continue
            date = parts[0]
            hour = parts[1]
            
            if Is_recent(date, hour, 2) :
                recent_good.add(yet_str(text, "**"))
            
            elif Is_recent(date, hour, 4) :
                recent_good.add(yet_str(text, "*"))
                
                
    recent_good_list = sorted(recent_good)
    
    total_list = yet_list + recent_good_list
    total_list = sorted(total_list, key=lambda s: (s.lower(), s))
    
    if yet_list or recent_good_list:
        total_message = "\n".join(total_list)
        full_message  = f"최근 축팩 및 미검증 리스트 {len(total_list)}\n(** : 2일 미만, * : 4일 미만)\n{total_message}"
        await safe_send(ctx, full_message, True)
    else:
        await ctx.send("축팩 및 미검증이 없습니다.")    

@bot.command()
async def add(ctx, name, code):
    if str(ctx.author.id) in Admin.DATA:
        Member.edit('+', name, code)
        Member.update()
        USER_DICT[name] = GIST.USER(name, code)
        logger.info(f"Member 에서 새로운 ID를 갱신했습니다! : {name}")
        await ctx.send(f"Member에 {name} 추가 하였습니다.")
    
@bot.command()
async def delete(ctx, name, code):
    if str(ctx.author.id) in Admin.DATA:
        Member.edit('-', name, code)
        Member.update()
        for Server in list(USER_DICT[name].Server):
            USER_DICT[name].offline(Server)
        USER_DICT.pop(name, None)
        logger.info(f"Member 에서 제거된 ID를 갱신했습니다! : {name}")
        await ctx.send(f"Member에 {name} 제거 하였습니다.")
    
@bot.command()
async def mandate(ctx, code):
    if str(ctx.author.id) in Admin.DATA:
        Admin.edit('+', code)
        Admin.update()
        logger.info(f"Author 에서 새로운 ID를 갱신했습니다! : {code}")
        await ctx.send(f"Author에 {code} 추가 하였습니다.")

@bot.command()
async def admin(ctx):
    if Admin.DATA:
        text = "\n".join(Admin.DATA)
        await ctx.send(f"```권한자 상태 ({len(Admin.DATA)}명):\n{text}```")
    else :
        await ctx.send("현재 권한이 있는 사람이 없습니다.")
        

@bot.command()
async def state(ctx):
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에 해주세요.")
        return

    text = '\n'.join([user.NAME for user in Server.ONLINE])
    
    if Server.ONLINE :
        await ctx.send(f"```현재 {Server.FILE.NAME}의 온라인 상태 ({len(Server.ONLINE)}명):\n{text}```")
    else :
        await ctx.send(f"```현재 {Server.FILE.NAME}에 온라인 상태인 사람이 없습니다.```")
        
@bot.command()
async def timer(ctx):
    for ID, Server in SERVER_DICT.items():
        Sorted_User = sorted(Server.ONLINE, key = lambda user : user.inform[ID]['TIME'])
        
        text = "\n".join([f"{user.NAME:<12}| {user.inform[ID]['TIME'].astimezone().strftime('%Y-%m-%d %H:%M:%S')}" for user in Sorted_User])
        
        if Server.ONLINE :
            await ctx.send(f"```현재 {Server.FILE.NAME}의 온라인 상태 ({len(Server.ONLINE)}명):\n{text}```")
        else :
            await ctx.send(f"```현재 {Server.FILE.NAME}에 온라인 상태인 사람이 없습니다.```")
            
    if str(ctx.author.id) in Admin.DATA:
        OFF_USER = [user for user in USER_DICT.values() if not user.Server and user.off]
        Sorted_User = sorted(OFF_USER, key = lambda user : user.lastoff())
        text = "\n".join([f"{user.NAME:<12}| {user.lastoff().astimezone().strftime('%Y-%m-%d %H:%M:%S')}" for user in Sorted_User])
        
        if OFF_USER :
            await ctx.send(f"```현재 오프라인 상태 ({len(OFF_USER)}명):\n{text}```")
        else :
            await ctx.send("```현재 오프라인 상태인 사람이 없습니다.```")
        
        REST_USER = [user for user in USER_DICT.values() if not user.Server and not user.off]
        text = "\n".join([f"{user.NAME}" for user in REST_USER])
        
        if REST_USER :
            await ctx.send(f"```현재 휴식 상태 ({len(REST_USER)}명):\n{text}```")
        else :
            await ctx.send("```현재 휴식 상태인 사람이 없습니다.```")
    
        

@bot.command()
async def member(ctx):
    try:
        if Member:
            num_member = len(Member.DATA)
            text = "\n".join([f"{key:<12}| {value}" for key, value in Member.DATA.items()])
            full_text = f"등록된 멤버 ({num_member}명):\n{text}"
            await safe_send(ctx, full_text, True)
        else:
            await ctx.send("등록된 멤버가 없습니다.")
    except Exception as e:
        logger.error("에러가 있습니다.", e)

@bot.command()
async def barracks(ctx):
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)

    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에 해주세요.")
        return
    
    ID = Server.ID
    Barracks    = {user.NAME : user.inform[ID].get('BARRACKS', 0) for user in Server.ONLINE}
    Mode        = {user.NAME : user.inform[ID].get('TYPE', None) for user in Server.ONLINE}
    Rate        = {user.NAME : user.inform[ID].get('AVG', 0.0) for user in Server.ONLINE}
    Select      = {user.NAME : user.inform[ID].get('SELECT', 0.0) for user in Server.ONLINE}

    if Server.ONLINE:
        num_on = len(Barracks)
        Type = {3 : [], 5: [], None: []}
        for name, barracks in sorted(Barracks.items(), key=lambda item : (item[1], Rate[item[0]]), reverse=True) :
            Type[Mode[name]].append(f"{name:<12}| {barracks:<2} 개 ({round(Rate[name], 2):<5})")
        
        total_barracks = sum(Barracks.values())
        total_rate = sum(x for x in Rate.values() if not math.isnan(x))

        try:
            Expand = {}
            for name, select in Select.items():
                if not math.isnan(Rate[name]):
                    for ex in select:
                        expand_rate = Rate[name]/len(select)
                        if Expand.get(ex, None):
                            Expand[ex] += expand_rate
                        else :
                            Expand[ex] = expand_rate
        except Exception as e:
            logger.error(name)
            logger.error(select)
            logger.error(e)
            
        text = f"현재 온라인 상태 ({num_on}명, 총 {total_barracks} 배럭 {round(total_rate,2):<5}Packs/min):\n"
        for key, value in Expand.items():
            text = text + f'{key:<10} : {round(value,2):<6}\n'
        text = text + '\n'
        text_dict = {}
        for key in Type.keys():
            text_dict[key] = "\n".join(Type[key])
            if Type[key] :
                text = text + f"<{key} Pack>\n{text_dict[key]}\n\n"

        await safe_send(ctx, text, True)

    else :
        await ctx.send(f"```현재 {Server.FILE.NAME}에 온라인 상태인 사람이 없습니다.```")
        
@bot.command()
async def alive(ctx):
    for Server in SERVER_DICT.values():
        text = Server.Health.strftime("%Y.%m.%d %H:%M:%S")
        await ctx.send(f"```{Server.FILE.NAME}의 마지막 점검\n{text}```")

# 테스트 전용 명령어들
@bot.command()
async def test_update(ctx):
    """테스트: 온라인 상태 즉시 업데이트"""
    if str(ctx.author.id) not in Admin.DATA:
        await ctx.send("관리자 권한이 필요합니다.")
        return
    
    await ctx.send("온라인 상태 업데이트 시작...")
    await do_update()
    await ctx.send("온라인 상태 업데이트 완료!")

@bot.command()
async def test_verify(ctx):
    """테스트: 갓팩 검증 즉시 실행"""
    if str(ctx.author.id) not in Admin.DATA:
        await ctx.send("관리자 권한이 필요합니다.")
        return
    
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에서 실행해주세요.")
        return
    
    await ctx.send(f"{Server.FILE.NAME} 갓팩 검증 시작...")
    await do_verify(Server)
    await ctx.send(f"{Server.FILE.NAME} 갓팩 검증 완료!")

@bot.command()
async def test_offline(ctx):
    """테스트: 오프라인 처리 즉시 실행"""
    if str(ctx.author.id) not in Admin.DATA:
        await ctx.send("관리자 권한이 필요합니다.")
        return
    
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에서 실행해주세요.")
        return
    
    await ctx.send(f"{Server.FILE.NAME} 오프라인 처리 시작...")
    await recent_offline(Server)
    await ctx.send(f"{Server.FILE.NAME} 오프라인 처리 완료!")

@bot.command()
async def test_recent_online(ctx):
    """테스트: recent_online 함수 실행"""
    if str(ctx.author.id) not in Admin.DATA:
        await ctx.send("관리자 권한이 필요합니다.")
        return
    
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에서 실행해주세요.")
        return
    
    await ctx.send(f"{Server.FILE.NAME} recent_online 시작...")
    await recent_online(Server)
    await ctx.send(f"{Server.FILE.NAME} recent_online 완료! Server.ONLINE: {len(Server.ONLINE)}명")

@bot.command()
async def test_recent_godpack(ctx):
    """테스트: recent_godpack 함수 실행"""
    if str(ctx.author.id) not in Admin.DATA:
        await ctx.send("관리자 권한이 필요합니다.")
        return
    
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에서 실행해주세요.")
        return
    
    await ctx.send(f"{Server.FILE.NAME} recent_godpack 시작...")
    await recent_godpack(Server)
    await ctx.send(f"{Server.FILE.NAME} recent_godpack 완료!")

@bot.command()
async def test_timeout(ctx):
    """테스트: 타임아웃 체크 즉시 실행"""
    if str(ctx.author.id) not in Admin.DATA:
        await ctx.send("관리자 권한이 필요합니다.")
        return
    
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에서 실행해주세요.")
        return
    
    await ctx.send(f"{Server.FILE.NAME} 타임아웃 체크 시작...")
    
    # do_update의 타임아웃 체크 부분만 실행
    now = datetime.now(timezone.utc)
    timeout_duration = timedelta(seconds=10) if TEST_MODE else timedelta(minutes=15)
    
    remove = []
    for user in Server.ONLINE:
        if now - user.inform[Server.ID]['TIME'] >= timeout_duration:
            remove.append(user)
            logger.info(f"⏰ {user.NAME}님이 타임아웃으로 오프라인 처리됩니다.")
    
    for user in remove:
        user.offline(Server)
    
    if remove:
        Server.FILE.update()
        await ctx.send(f"타임아웃으로 {len(remove)}명이 오프라인 처리되었습니다.")
    else:
        await ctx.send("타임아웃된 사용자가 없습니다.")

@bot.command()
async def test_gist_sync(ctx):
    """테스트: GIST 동기화 상태 확인"""
    if str(ctx.author.id) not in Admin.DATA:
        await ctx.send("관리자 권한이 필요합니다.")
        return
    
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에서 실행해주세요.")
        return
    
    await ctx.send(f"{Server.FILE.NAME} GIST 동기화 상태 확인 중...")
    
    # WAITING과 ONLINE 상태 확인
    raw_data = Server.FILE.fetch_raw()
    
    embed = discord.Embed(title=f"{Server.FILE.NAME} 동기화 상태", color=discord.Color.blue())
    embed.add_field(name="Server.FILE.DATA", value=f"{len(Server.FILE.DATA)}명", inline=True)
    embed.add_field(name="GIST 파일", value=f"{len(raw_data)}명", inline=True)
    embed.add_field(name="Server.ONLINE", value=f"{len(Server.ONLINE)}명", inline=True)
    embed.add_field(name="Server.WAITING", value=f"{len(Server.WAITING)}명", inline=True)
    
    # 동기화 차이 확인
    in_file_not_online = Server.FILE.DATA - {user.CODE for user in Server.ONLINE}
    if in_file_not_online:
        embed.add_field(name="파일에만 있음", value=f"{len(in_file_not_online)}명", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def test_clean_forum(ctx):
    """테스트: 포럼 정리 작업 실행"""
    if str(ctx.author.id) not in Admin.DATA:
        await ctx.send("관리자 권한이 필요합니다.")
        return
    
    Server = next((S for S in SERVER_DICT.values() if ctx.channel.id == S.COMMAND), None)
    if Server is None:
        await ctx.send("해당 명령어는 명령어 채널에서 실행해주세요.")
        return
    
    await ctx.send(f"{Server.FILE.NAME} 포럼 정리 시작...")
    
    # do_verify의 포럼 정리 부분만 실행
    forum_channel = await bot.fetch_channel(Server.POSTING)
    threads = forum_channel.threads
    
    deleted_count = 0
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(hours=24*7)
    
    for thread in threads.copy():
        thread_tags_ids = [tag.id for tag in thread.applied_tags]
        
        if Server.Tag["Bad"] in thread_tags_ids:
            try:
                parts = thread.name.split()
                KST = timezone(timedelta(hours=9))
                time_str = f"{parts[7]} {parts[8]}"
                thread_created_at = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=KST)
            except:
                thread_created_at = thread.created_at
                
            if thread_created_at < one_week_ago:
                deleted_count += 1
                logger.info(f"삭제 예정: {thread.name}")
    
    await ctx.send(f"1주일 이상된 Bad 태그 스레드: {deleted_count}개 발견")
        
                
    
    

async def main():
    # 필요한 디렉토리 생성 (Poke.py는 Gist를 사용하므로 로컬 디렉토리는 최소한만)
    ensure_directories()
    
    # 테스트 모드에서 자동 종료 설정
    is_test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    if is_test_mode:
        test_duration = int(os.getenv('TEST_DURATION', '1000')) 
        logger.info(f"[TEST MODE] Bot will auto-shutdown after {test_duration} seconds")
        asyncio.create_task(auto_shutdown(test_duration))
    
    asyncio.create_task(update_periodic())
    
    for Server in SERVER_DICT.values() :
        asyncio.create_task(verify_periodic(Server))
    async with bot:
        await bot.start(DISCORD_TOKEN)

async def auto_shutdown(duration):
    """테스트 모드에서 지정된 시간 후 봇을 종료"""
    await asyncio.sleep(duration)
    logger.info(f"[TEST MODE] Auto-shutdown after {duration} seconds")
    await bot.close()
    # 강제 종료를 위한 추가 조치
    os._exit(0)

if __name__ == "__main__":
    asyncio.run(main())
            
        
