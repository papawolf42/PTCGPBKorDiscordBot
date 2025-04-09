import discord
import asyncio
import requests
import time
import json
import re
import math
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from GIST import FILE, TEXT, JSON, USER, SERVER

MAIN_CHANNEL = os.getenv('DISCORD_MAIN_CHANNEL_ID')

# 멤버 관련 설정
ID   = "os.getenv('GIST_ID_1')"
NAME = "Alliance"
Member = JSON(ID, NAME)

ID   = "os.getenv('GIST_ID_1')"
NAME = "Admin"
Admin = TEXT(ID, NAME)


# 서버 설정 공간
SERVER_DICT = {}

ID   = "os.getenv('GIST_ID_2')"
NAME = "Group1"
Group1 = TEXT(ID, NAME, False)

ID   = "os.getenv('GIST_ID_3')"
NAME = "GodPack1"
GodPack1 = JSON(ID, NAME)

ID      = os.getenv('DISCORD_GROUP1_HEARTBEAT_ID')
DETECT  = os.getenv('DISCORD_GROUP1_DETECT_ID')
POSTING = os.getenv('DISCORD_GROUP1_POSTING_ID')
COMMAND = os.getenv('DISCORD_GROUP1_COMMAND_ID')
MUSEUM  = os.getenv('DISCORD_GROUP1_MUSEUM_ID')
TAG = {
        "Yet"    : os.getenv('DISCORD_GROUP1_TAG_YET'),
        "Good"   : os.getenv('DISCORD_GROUP1_TAG_GOOD'),
        "Bad"    : os.getenv('DISCORD_GROUP1_TAG_BAD'),
        "1P"     : os.getenv('DISCORD_GROUP1_TAG_1P'),
        "2P"     : os.getenv('DISCORD_GROUP1_TAG_2P'),
        "3P"     : os.getenv('DISCORD_GROUP1_TAG_3P'),
        "4P"     : os.getenv('DISCORD_GROUP1_TAG_4P'),
        "5P"     : os.getenv('DISCORD_GROUP1_TAG_5P'),
        "Notice" : os.getenv('DISCORD_GROUP1_TAG_NOTICE')
}
SERVER_DICT[ID] = SERVER(ID, Group1, GodPack1, DETECT, POSTING, COMMAND, MUSEUM, TAG)



ID   = "os.getenv('GIST_ID_2')"
NAME = "Group2"
Group2 = TEXT(ID, NAME, False)

ID   = "os.getenv('GIST_ID_3')"
NAME = "GodPack2"
GodPack2 = JSON(ID, NAME)

ID      = 1356566217187528804
DETECT  = 1356566139039121408
POSTING = 1356565996466339861
COMMAND = 1356656481180848195
MUSEUM  = 1356566293050036316
TAG = {
        "Yet"    : 1356632239622066489,
        "Good"   : 1356632028526678108,
        "Bad"    : 1356632066795765760,
        "1P"     : 1356631731154980912,
        "2P"     : 1356631845499961354,
        "3P"     : 1356631886142898327,
        "4P"     : 1356631923727798325,
        "5P"     : 1356631984855711856,
        "Notice" : 1356632159804461215
}
SERVER_DICT[ID] = SERVER(ID, Group2, GodPack2, DETECT, POSTING, COMMAND, MUSEUM, TAG)



ID   = "os.getenv('GIST_ID_2')"
NAME = "Group3"
Group3 = TEXT(ID, NAME, False)

ID   = "os.getenv('GIST_ID_3')"
NAME = "GodPack3"
GodPack3 = JSON(ID, NAME)

ID      = os.getenv('DISCORD_GROUP3_HEARTBEAT_ID')
DETECT  = os.getenv('DISCORD_GROUP3_DETECT_ID')
POSTING = os.getenv('DISCORD_GROUP3_POSTING_ID')
COMMAND = os.getenv('DISCORD_GROUP3_COMMAND_ID')
MUSEUM  = os.getenv('DISCORD_GROUP3_MUSEUM_ID')
TAG = {
        "Yet"    : os.getenv('DISCORD_GROUP3_TAG_YET'),
        "Good"   : os.getenv('DISCORD_GROUP3_TAG_GOOD'),
        "Bad"    : os.getenv('DISCORD_GROUP3_TAG_BAD'),
        "1P"     : os.getenv('DISCORD_GROUP3_TAG_1P'),
        "2P"     : os.getenv('DISCORD_GROUP3_TAG_2P'),
        "3P"     : os.getenv('DISCORD_GROUP3_TAG_3P'),
        "4P"     : os.getenv('DISCORD_GROUP3_TAG_4P'),
        "5P"     : os.getenv('DISCORD_GROUP3_TAG_5P'),
        "Notice" : os.getenv('DISCORD_GROUP3_TAG_NOTICE')
}
SERVER_DICT[ID] = SERVER(ID, Group3, GodPack3, DETECT, POSTING, COMMAND, MUSEUM, TAG)



ID   = "os.getenv('GIST_ID_2')"
NAME = "Group4"
Group4 = TEXT(ID, NAME, False)

ID   = "os.getenv('GIST_ID_3')"
NAME = "GodPack4"
GodPack4 = JSON(ID, NAME)

ID      = 1358035181260242965
DETECT  = 1358035153959649393
POSTING = 1358035020354158663
COMMAND = 1358035085722390658
MUSEUM  = 1358035213845922033
TAG = {
        "Yet"    : 1358035845889786015,
        "Good"   : 1358035893797126156,
        "Bad"    : 1358035937040404642,
        "1P"     : 1358035423171182703,
        "2P"     : 1358035547217596467,
        "3P"     : 1358035601127116873,
        "4P"     : 1358035648568885379,
        "5P"     : 1358035696652390610,
        "Notice" : 1358035798854865048
}
SERVER_DICT[ID] = SERVER(ID, Group4, GodPack4, DETECT, POSTING, COMMAND, MUSEUM, TAG)



ID   = "os.getenv('GIST_ID_2')"
NAME = "Group5"
Group5 = TEXT(ID, NAME, False)

ID   = "os.getenv('GIST_ID_3')"
NAME = "GodPack5"
GodPack5 = JSON(ID, NAME)

ID      = 1358091689742438522
DETECT  = 1358091656762753187
POSTING = 1358091549329588254
COMMAND = 1358091614114812194
MUSEUM  = 1358091791936655500
TAG = {
        "Yet"    : 1358092190147936453,
        "Good"   : 1358092163761705202,
        "Bad"    : 1358092171605053547,
        "1P"     : 1358092115107643512,
        "2P"     : 1358092125006462976,
        "3P"     : 1358092134103650314,
        "4P"     : 1358092142668681388,
        "5P"     : 1358092155230621928,
        "Notice" : 1358092199740571828
}
SERVER_DICT[ID] = SERVER(ID, Group5, GodPack5, DETECT, POSTING, COMMAND, MUSEUM, TAG)



ID   = "os.getenv('GIST_ID_2')"
NAME = "Group6"
Group6 = TEXT(ID, NAME, False)

ID   = "os.getenv('GIST_ID_3')"
NAME = "GodPack6"
GodPack6 = JSON(ID, NAME)

ID      = os.getenv('DISCORD_GROUP6_HEARTBEAT_ID')
DETECT  = os.getenv('DISCORD_GROUP6_DETECT_ID')
POSTING = os.getenv('DISCORD_GROUP6_POSTING_ID')
COMMAND = os.getenv('DISCORD_GROUP6_COMMAND_ID')
MUSEUM  = os.getenv('DISCORD_GROUP6_MUSEUM_ID')
TAG = {
        "Yet"    : os.getenv('DISCORD_GROUP6_TAG_YET'),
        "Good"   : os.getenv('DISCORD_GROUP6_TAG_GOOD'),
        "Bad"    : os.getenv('DISCORD_GROUP6_TAG_BAD'),
        "1P"     : os.getenv('DISCORD_GROUP6_TAG_1P'),
        "2P"     : os.getenv('DISCORD_GROUP6_TAG_2P'),
        "3P"     : os.getenv('DISCORD_GROUP6_TAG_3P'),
        "4P"     : os.getenv('DISCORD_GROUP6_TAG_4P'),
        "5P"     : os.getenv('DISCORD_GROUP6_TAG_5P'),
        "Notice" : os.getenv('DISCORD_GROUP6_TAG_NOTICE')
}
SERVER_DICT[ID] = SERVER(ID, Group6, GodPack6, DETECT, POSTING, COMMAND, MUSEUM, TAG)


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
    USER_DICT[name] = USER(name, code)
    
    
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
            print(f"⚠️ 메시지 가져오기 실패 (시도 {attempt + 1}/{retries}): {e}")
            await asyncio.sleep(2 ** attempt)
    print(f"⛔ 최종 실패: {thread.name}")
    return None

async def safe_fetch_channel(channel, retries=5):
    for attempt in range(retries):
        try:
            return bot.fetch_channel(channel)
        except Exception as e:
            print(f"⚠️ 채널 가져오기 실패 (시도 {attempt + 1}/{retries}): {e}")
            await asyncio.sleep(2 ** attempt)
    print(f"⛔ 최종 실패: {channel}")
    return None

async def recent_godpack(Server):
    now = datetime.now(timezone.utc)
    day = 4
    days_ago = now - timedelta(hours=24*day)
    
    print(f"채널 ID: {Server.DETECT}에서 {day}일 이내 메시지 조회 시작")
    channel = await bot.fetch_channel(Server.DETECT)
    try:
        messages = [msg async for msg in channel.history(limit=1000)]
        print(f"총 {len(messages)}개의 메시지를 확인했습니다.")

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

        print(f"최근 {day}일 이내 감지된 레어팩 수: {detected_gp}개")
        Server.GODPACK.update()
        
    except Exception as e:
        print(f"❌ 메시지 불러오는 중 오류 발생: {e}")


async def recent_online(Server):
    now = datetime.now(timezone.utc)
    
    Threshold = {'Off' : now - timedelta(minutes=15),
                 'Rest': now - timedelta(hours=24*7)}

    channel = await bot.fetch_channel(Server.ID)
    
    print(f"채널 ID: {Server.ID}에서 최근 메시지 조회 시작")
    try:
        messages = [msg async for msg in channel.history(limit=500)]
        print(f"총 {len(messages)}개의 메시지를 확인했습니다.")
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

        print(f"✅ 최근 15분 이내에 감지된 온라인 유저 수: {len(Server.FILE.DATA)}명")
        Server.FILE.update()
        
    except Exception as e:
        print(f"❌ 메시지 불러오는 중 오류 발생: {e}")

async def recent_offline(Server):
    now = datetime.now(timezone.utc)
    
    Threshold = {'Off' : now - timedelta(minutes=15),
                 'Rest': now - timedelta(hours=24*7)}

    channel = await bot.fetch_channel(Server.ID)
    
    print(f"채널 ID: {Server.ID}에서 오래된 메시지 조회 시작")
    try:
        messages_old = [msg async for msg in channel.history(limit=50000)]
        print(f"총 {len(messages_old)}개의 메시지를 확인했습니다.")
        for message in messages_old :
            if "Online:" in message.content:
                if message.created_at < Threshold["Off"] and message.created_at >= Threshold["Rest"] :
                    name = message.content.split("\n")[0].strip()
                    if name in USER_DICT.keys():
                        if USER_DICT[name].CODE not in Server.FILE.DATA and USER_DICT[name].off.get(Server.ID, None) is None:
                            USER_DICT[name].offlined(Server, message)
                            
        print("오프라인 유저를 모두 확인했습니다.")
    except Exception as e:
        print(f"❌ 메시지 불러오는 중 오류 발생: {e}")
        
        
async def update_periodic():
    Server_Channel = {ID : await bot.fetch_channel(ID) for ID, Server in SERVER_DICT.items()}
        
    while True:
        await asyncio.sleep(30)
            
        RAW_GIST_DICT = {}
        for ID, Server in SERVER_DICT.items() :
            RAW_GIST_DICT[ID] = Server.FILE.fetch_raw()
            for user in list(Server.WAITING) :
                if user.CODE in RAW_GIST_DICT[ID] :
                    Server.WAITING.discard(user)
                    Server.ONLINE.add(user)
                    print(f"{user.NAME} 님이 GIST에 업데이트 되었습니다!")
                    await Server_Channel[ID].send(f"{user.NAME} 님이 GIST에 업데이트 되었습니다!")
                else :
                    print(f"{user.NAME} 님의 GIST 업데이트 대기 중...")
                    await Server_Channel[ID].send(f"{user.NAME} 님의 GIST 업데이트 대기 중...")


async def delete_thread(Server):
    while True:
        await asyncio.sleep(60)
        
        forum_channel = await bot.fetch_channel(Server.POSTING)
        
        threads = forum_channel.threads
        

        async for thread in forum_channel.archived_threads(limit=100):
            try:
                if thread.archived:
                    await thread.edit(archived=False)
                    await asyncio.sleep(1)
                threads.append(thread)
            except Exception as e:
                print(f"❌ 스레드 {thread.name} 복원 중 오류 발생: {e}")
    
        for thread in threads :
            thread_tags_ids = [tag.id for tag in thread.applied_tags]
            
            now = datetime.now(timezone.utc)
            if Server.FILE.NAME in ['Group4', 'Group5']:
                one_week_ago = now - timedelta(hours=24)
            else :
                one_week_ago = now - timedelta(hours=24*7)
            if Server.Tag["Bad"] in thread_tags_ids :
                try :
                    parts = thread.name.split()
                    KST = timezone(timedelta(hours=9))
                    time_str = f"{parts[7]} {parts[8]}"
                    thread_created_at = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=KST)
                except :
                    thread_created_at = thread.created_at
                
                if thread_created_at < one_week_ago :
                    try :
                        print(f"{thread.name}이 삭제 됩니다.")
                        await thread.delete()
                        await asyncio.sleep(5)
                    except Exception as e:
                        print(f"{thread.name} 삭제에 실패했습니다", e)


async def verify_periodic(Server):
    while True:
        await asyncio.sleep(120)
        Server.Health = datetime.now(timezone.utc) + timedelta(hours=9)
        
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
                print(f"❌ 스레드 {thread.name} 복원 중 오류 발생: {e}")
        
            
        for thread in threads.copy() :
            thread_tags_ids = [tag.id for tag in thread.applied_tags]
            
            now = datetime.now(timezone.utc)
            if Server.FILE.NAME in ['Group4', 'Group5']:
                one_week_ago = now - timedelta(hours=24)
            else :
                one_week_ago = now - timedelta(hours=24*7)
            if Server.Tag["Bad"] in thread_tags_ids :
                try :
                    parts = thread.name.split()
                    KST = timezone(timedelta(hours=9))
                    time_str = f"{parts[7]} {parts[8]}"
                    thread_created_at = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=KST)
                except :
                    thread_created_at = thread.created_at
                    
                if thread_created_at < one_week_ago :
                    try :
                        print(f"{thread.name}이 삭제 됩니다.")
                        await thread.delete()
                        await asyncio.sleep(5)
                        threads.remove(thread)
                    except Exception as e:
                        print(f"{thread.name} 삭제에 실패했습니다", e)
                        
            

        THREAD_DICT = {"Yet":[], "Bad":[], "Good":[], "Notice":[], "Error":[]}
        
        for thread in threads :
            thread_name = thread.name
            thread_tags = thread.applied_tags
            
            thread_tags_ids = [tag.id for tag in thread_tags]
            
            if Server.Tag["Notice"] in thread_tags_ids :
                THREAD_DICT["Notice"].append(thread)
                
            elif Server.Tag["Yet"] in thread_tags_ids :
                now = datetime.now(timezone.utc)
                one_ago   = now - timedelta(hours=12)
                two_ago   = now - timedelta(hours=24)
                three_ago = now - timedelta(hours=36)
                
                if Server.FILE.NAME in ['Group4', 'Group5']:
                    time_threshold = {"1P" : two_ago, "2P" : two_ago, "3P" : two_ago,
                                      "4P" : two_ago, "5P" : two_ago}
                else :
                    time_threshold = {"1P" : two_ago, "2P" : two_ago, "3P" : two_ago,
                                      "4P" : three_ago, "5P" : three_ago}
                
                bad_threshold  = {"2P" : 5, "3P" : 8, "4P" : 11, "5P" : 14}
                
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
                    
                    if no >= 3 and bad == 0 :
                        if thread_created_at < one_ago :
                            tag_id = Server.Tag["Bad"]
                            bad_tag = next((tag for tag in forum_tags if tag.id == tag_id), None)
                            THREAD_DICT["Bad"].append(thread)
                            await thread.edit(applied_tags = [bad_tag])
                        else :
                            THREAD_DICT["Yet"].append(thread)
                        
                    
                    elif pack in ["2P", "3P", "4P", "5P"] :
                        if thread_created_at < time_threshold[pack] or bad >= bad_threshold[pack] :
                            tag_id = Server.Tag["Bad"]
                            bad_tag = next((tag for tag in forum_tags if tag.id == tag_id), None)
                            THREAD_DICT["Bad"].append(thread)
                            await thread.edit(applied_tags = [bad_tag])
                        else :
                            THREAD_DICT["Yet"].append(thread)
                    
                    elif pack == "1P" :
                        if thread_created_at < time_threshold[pack] :
                            tag_id = Server.Tag["Bad"]
                            bad_tag = next((tag for tag in forum_tags if tag.id == tag_id), None)
                            THREAD_DICT["Bad"].append(thread)
                            await thread.edit(applied_tags = [bad_tag])
                        else :
                            THREAD_DICT["Yet"].append(thread)
            
                    else :
                        print(f"유효하지 않은 포스트가 검증 채널에 있습니다.\n제목 : {thread_name}")
                        await alert_channel.send(f"유효하지 않은 포스트가 검증 채널에 있습니다.\n제목 : {thread_name}")
                    
            elif Server.Tag["Bad"] in thread_tags_ids :
                THREAD_DICT["Bad"].append(thread)

            elif Server.Tag["Good"] in thread_tags_ids :
                THREAD_DICT["Good"].append(thread)
                    
            else :
                print(f"유효하지 않은 포스트가 검증 채널에 있습니다.\n제목 : {thread_name}")
                await alert_channel.send(f"유효하지 않은 포스트가 검증 채널에 있습니다.\n제목 : {thread_name}")

        
        yet_list = [text for text, verify in Server.GODPACK.DATA.items() if verify == 'Yet']
        
        for text in yet_list :
            parts = text.split()
            title = f"{parts[2]} {parts[3]} / {parts[4]} / {parts[5]} / {parts[0]} {parts[1]}"
            if title in [temp.name for temp in THREAD_DICT["Yet"]] :
                continue
            else :
                if title in [temp.name for temp in THREAD_DICT["Good"]] :
                    thread = next((temp for temp in THREAD_DICT["Good"] if title == temp.name), None)
                    Server.GODPACK.edit('+', text, "Good")
                    print(f"❗❗ {parts[2]} {parts[3]} 은 축으로 검증 되었습니다.")
                    await alert_channel.send(f"🎉 {parts[2]} {parts[3]} 은 축으로 검증 되었습니다.")
                    await main_channel.send(f"🎉 {parts[2]} {parts[3]} 은 축으로 검증 되었습니다. ({Server.FILE.NAME})")
                    try:
                        museum_channel = await bot.fetch_channel(Server.MUSEUM)
                        await Server.post_museum(thread, museum_channel)
                    except Exception as e:
                        print(f"{title} 박물관 전시 실패! ", e)
                
                elif title in [temp.name for temp in THREAD_DICT["Bad"]] :
                    Server.GODPACK.edit('+', text, "Bad") 
                    print(f"❗❗ {parts[2]} {parts[3]} 은 망으로 검증 되었습니다.")
                    await alert_channel.send(f"❗❗ {parts[2]} {parts[3]} 은 망으로 검증 되었습니다.")
                elif title in [temp.name for temp in THREAD_DICT["Error"]] :
                    print(f"❗❗ {parts[2]} {parts[3]} 에 오류가 있습니다.")
                else :
                    KST = timezone(timedelta(hours=9))
                    timenow = datetime.now(KST)

                    time_str = f"{parts[0]} {parts[1]}"
                    parsed_time = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=KST)
                    
                    if abs(timenow - parsed_time) <= timedelta(minutes=10) :
                        continue
                    
                    print(f"⚠️{title} 포스트를 찾을 수 없습니다.")
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
                        print(f"❌ 메시지 불러오는 중 오류 발생: {e}")
                    try:
                        await Server.Post(forum_channel, images, inform, title)
                    except Exception as e:
                        print(f"{title} 포스팅 실패 : ", e)
                    await asyncio.sleep(5)
        Server.GODPACK.update()
            
                        

@bot.event
async def on_ready():
    print(f"✅ 로그인됨: {bot.user}")
    
    for server in SERVER_DICT.values():
        await recent_online(server)
    for server in SERVER_DICT.values():
        await recent_godpack(server)
        await asyncio.sleep(60)
    for server in SERVER_DICT.values():
        await recent_offline(server)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)
    
    if message.channel.id in SERVER_DICT:
        if "Online:" in message.content:
            Server = SERVER_DICT[message.channel.id]
            name = message.content.split("\n")[0].strip()
            if name in USER_DICT.keys():
                if Server.FILE.NAME == 'Group6':
                    Group1_Server = SERVER_DICT[os.getenv('DISCORD_GROUP1_HEARTBEAT_ID')]
                    USER_DICT[name].called(Group1_Server, message)
                    if USER_DICT[name].CODE not in Group1_Server.FILE.DATA:
                        USER_DICT[name].online(Group1_Server)
                        Group1_Server.FILE.update()
                    
                    Group3_Server = SERVER_DICT[os.getenv('DISCORD_GROUP3_HEARTBEAT_ID')]
                    USER_DICT[name].called(Group3_Server, message)
                    if USER_DICT[name].CODE not in Group3_Server.FILE.DATA:
                        USER_DICT[name].online(Group3_Server)
                        Group3_Server.FILE.update()
                        
                USER_DICT[name].called(Server, message)
                if USER_DICT[name].CODE not in Server.FILE.DATA:
                    print(f"✅ 수집된 이름: {name}, 코드 : {USER_DICT[name].CODE}")
                    USER_DICT[name].online(Server)
                    Server.FILE.update()
                    await message.channel.send(f"로그인 시도 : {name}")
                    await message.channel.send("GIST 업데이트까지 약 5분 정도 소요됩니다.")
                
            else :
                await message.channel.send(f"{name} 은 ID 목록에 없습니다.")
            
            try :
                now = datetime.now(timezone.utc)
                remove = [user for user in Server.ONLINE if now - user.inform[Server.ID]['TIME'] >= timedelta(minutes=15)]
                
                if remove :
                    for user in remove :
                        user.offline(Server)
                        print(f"{user.NAME} 님이 OFF-LINE 되었습니다.")
                        Server.FILE.update()
                        await message.channel.send(f"{user.NAME} 님이 OFF-LINE 되었습니다.")
                        
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
    
    
    if message.channel.id in [Server.DETECT for Server in SERVER_DICT.values()] :
        for Server in SERVER_DICT.values():
            if message.channel.id == Server.DETECT:
                break
        """
        if Server.FILE.NAME == 'Group1':
            Another = SERVER_DICT[os.getenv('DISCORD_GROUP3_HEARTBEAT_ID')]
        elif Server.FILE.NAME == 'Group3':
            Another = SERVER_DICT[os.getenv('DISCORD_GROUP1_HEARTBEAT_ID')]
        else :
            Another = None
        """
        Another = None
        if "Invalid" in message.content:
            print("Invalid God Pack 을 찾았습니다.")
            return
        
        elif "found by" in message.content:
            print("Pseudo God Pack 을 찾았습니다.")
            inform, title = Server.found_Pseudo(message)
            if Another :
                inform_, title_ = Another.found_Pseudo(message)
            
            if inform and title :
                images = message.attachments
                forum_channel = bot.get_channel(Server.POSTING)
                await Server.Post(forum_channel, images, inform, title)
                if Another :
                    forum_channel = bot.get_channel(Another.POSTING)
                    await Another.Post(forum_channel, images, inform, title)
            else :
                print("메시지에 오류가 있었습니다")

        
        elif "Valid" in message.content :
            print("God Pack 을 찾았습니다!")
            inform, title = Server.found_GodPack(message)
            if Another :
                inform_, title_ = Another.found_GodPack(message)
            
            if inform and title :
                images = message.attachments
                forum_channel = bot.get_channel(Server.POSTING)
                await Server.Post(forum_channel, images, inform, title)
                if Another :
                    forum_channel = bot.get_channel(Another.POSTING)
                    await Another.Post(forum_channel, images, inform, title)
            else :
                print("메시지에 오류가 있었습니다")
                
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
        print("에러가 있습니다.", e)

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
            print(f"❌ 스레드 {thread.name} 복원 중 오류 발생: {e}")

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
        USER_DICT[name] = USER(name, code)
        print(f"Member 에서 새로운 ID를 갱신했습니다! : {name}")
        await ctx.send(f"Member에 {name} 추가 하였습니다.")
    
@bot.command()
async def delete(ctx, name, code):
    if str(ctx.author.id) in Admin.DATA:
        Member.edit('-', name, code)
        Member.update()
        for Server in list(USER_DICT[name].Server):
            USER_DICT[name].offline(Server)
        USER_DICT.pop(name, None)
        print(f"Member 에서 제거된 ID를 갱신했습니다! : {name}")
        await ctx.send(f"Member에 {name} 제거 하였습니다.")
    
@bot.command()
async def mandate(ctx, code):
    if str(ctx.author.id) in Admin.DATA:
        Admin.edit('+', code)
        Admin.update()
        print(f"Author 에서 새로운 ID를 갱신했습니다! : {code}")
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
        print("에러가 있습니다.", e)

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
        
        Expand = {}
        for name, select in Select.items():
            if not math.isnan(Rate[name]):
                for ex in select:
                    expand_rate = Rate[name]/len(select)
                    if Expand.get(ex, None):
                        Expand[ex] += expand_rate
                    else :
                        Expand[ex] = expand_rate
        
        text = f"현재 온라인 상태 ({num_on}명, 총 {total_barracks} 배럭 {round(total_rate,2):<5}Packs/min):\n"
        for key, value in Expand.items():
            text = text + f'{key:<10} : {round(value,2):<6}\n'
        text = text + '\n'
        text_dict = {}
        for key in Type.keys():
            text_dict[key] = "\n".join(Type[key])
            if Type[key] :
                text = text + f"<{key} Pack>\n{text_dict[key]}\n\n"
        
        text = "```" + text + "```"
        
        await ctx.send(text)
    else :
        await ctx.send(f"```현재 {Server.FILE.NAME}에 온라인 상태인 사람이 없습니다.```")
        
@bot.command()
async def alive(ctx):
    for Server in SERVER_DICT.values():
        text = Server.Health.strftime("%Y.%m.%d %H:%M:%S")
        await ctx.send(f"```{Server.FILE.NAME}의 마지막 점검\n{text}```")
        
                
    
    

async def main():
    asyncio.create_task(update_periodic())
    
    for Server in SERVER_DICT.values() :
        asyncio.create_task(verify_periodic(Server))
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
            
        

