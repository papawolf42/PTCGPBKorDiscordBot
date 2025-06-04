import discord
import asyncio
import time
import re
from datetime import datetime, timedelta, timezone
import json
import requests

# Discord 설정
DISCORD_TOKEN = "***REMOVED***"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True
bot = discord.Client(intents=intents)

# Group4와 Group5 설정
SERVER_CONFIG = {
    # Group4
    1358035181260242965: {
        "name": "Group4",
        "detect_channel": 1358035153959649393,
        "posting_channel": 1358035020354158663,
        "command_channel": 1358035085722390658,
        "tags": {
            "Yet": 1358035845889786015,
            "Bad": 1358035937040404642,
            "Good": 1358035893797126156
        }
    },
    # Group5 추가
    1358091689742438522: {
        "name": "Group5",
        "detect_channel": 1358091656762753187,
        "posting_channel": 1358091549329588254,
        "command_channel": 1358091614114812194,
        "tags": {
            "Yet": 1358092190147936453,
            "Bad": 1358092171605053547,
            "Good": 1358092163761705202
        }
    }
}

# 설정 변수
DELETE_INTERVAL = 5  # 처리 주기 (초 단위)
HOURS_AGO = 12       # 몇 시간 지난 포스트를 대상으로 할지

@bot.event
async def on_ready():
    print(f"봇이 로그인했습니다: {bot.user}")
    print(f"설정: Group4, Group5 서버 적용, {HOURS_AGO}시간 기준으로 설정됨, 처리 주기: {DELETE_INTERVAL}초")
    
    # 아래 두 태스크 중 하나만 주석 해제하여 사용
    # 1. Yet -> Bad 변경 태스크
    asyncio.create_task(convert_yet_to_bad())
    
    # 2. Bad 삭제 태스크
    # asyncio.create_task(delete_bad_posts())

def extract_datetime_from_title(title):
    """
    포스트 제목에서 날짜와 시간 정보를 추출
    예: 'dele 735 / 20% / 2P / 2025.04.06 05:58' -> '2025.04.06 05:58'
    """
    try:
        # 정규표현식으로 날짜와 시간 패턴 추출
        match = re.search(r'(\d{4}\.\d{2}\.\d{2}\s\d{2}:\d{2})', title)
        if match:
            date_time_str = match.group(1)
            # 한국 시간 기준 datetime 객체로 변환
            kst = timezone(timedelta(hours=9))
            date_time_obj = datetime.strptime(date_time_str, "%Y.%m.%d %H:%M").replace(tzinfo=kst)
            return date_time_obj
    except Exception as e:
        print(f"❌ 제목에서 시간 추출 중 오류: {e}, 제목: {title}")
    return None

async def find_old_posts(server_id):
    """
    설정된 시간(HOURS_AGO)이 지난 Bad나 Yet으로 체크된 모든 포스트를 찾는 함수
    제목에 포함된 시간 정보를 기준으로 함
    """
    server_config = SERVER_CONFIG.get(server_id)
    if not server_config:
        print(f"서버 ID {server_id}에 대한 설정이 없습니다.")
        return {"bad": [], "yet": [], "forum_tags": []}

    print(f"{server_config['name']}에서 오래된 포스트 검색 시작")
    
    try:
        forum_channel = bot.get_channel(server_config['posting_channel'])
        if not forum_channel:
            forum_channel = await bot.fetch_channel(server_config['posting_channel'])
        
        threads = forum_channel.threads
        
        async for thread in forum_channel.archived_threads(limit=100):
            try:
                if thread.archived:
                    await thread.edit(archived=False)
                    await asyncio.sleep(1)
                threads.append(thread)
            except Exception as e:
                print(f"❌ 스레드 {thread.name} 복원 중 오류 발생: {e}")
        
        bad_posts = []  # Bad 태그 포스트
        yet_posts = []  # Yet 태그 포스트
        
        now = datetime.now(timezone(timedelta(hours=9)))  # 한국 시간 기준
        hours_ago = now - timedelta(hours=HOURS_AGO)
        
        for thread in threads:
            thread_tags_ids = [tag.id for tag in thread.applied_tags]
            
            # 제목에서 시간 추출
            title_datetime = extract_datetime_from_title(thread.name)
            
            # 제목에서 시간을 추출할 수 없는 경우는 스킵
            if not title_datetime:
                continue
            
            # 제목의 시간이 HOURS_AGO보다 이전인 경우
            if title_datetime < hours_ago:
                # 서버 생성 시간 (참고용)
                created_time = thread.created_at.astimezone() + timedelta(hours=9)
                # 제목 기준 시간과 현재 시간의 차이
                time_diff = now - title_datetime
                hours_diff = time_diff.total_seconds() / 3600
                
                post_info = {
                    "thread": thread,
                    "title_datetime": title_datetime,
                    "created_at": created_time,
                    "hours_passed": hours_diff,
                    "tags": thread_tags_ids
                }
                
                # Bad 태그가 있는 경우
                if server_config['tags']['Bad'] in thread_tags_ids:
                    bad_posts.append(post_info)
                # Yet 태그가 있는 경우
                elif server_config['tags']['Yet'] in thread_tags_ids:
                    yet_posts.append(post_info)
        
        # 제목 시간 기준으로 오래된 것부터 정렬
        bad_posts.sort(key=lambda p: p["title_datetime"])
        yet_posts.sort(key=lambda p: p["title_datetime"])
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {server_config['name']}에서:")
        print(f"  - Bad 태그 오래된 포스트: {len(bad_posts)}개")
        print(f"  - Yet 태그 오래된 포스트: {len(yet_posts)}개")
        
        # 포스트 정보 미리보기 출력
        if bad_posts:
            print("Bad 태그 포스트 목록:")
            for i, post in enumerate(bad_posts[:3]):
                thread = post["thread"]
                title_time = post["title_datetime"].strftime('%Y-%m-%d %H:%M')
                print(f"  {i+1}. '{thread.name}' - 제목 시간: {title_time}, 경과: {post['hours_passed']:.1f}시간")
            if len(bad_posts) > 3:
                print(f"  ... 외 {len(bad_posts) - 3}개")

        if yet_posts:
            print("Yet 태그 포스트 목록:")
            for i, post in enumerate(yet_posts[:3]):
                thread = post["thread"]
                title_time = post["title_datetime"].strftime('%Y-%m-%d %H:%M')
                print(f"  {i+1}. '{thread.name}' - 제목 시간: {title_time}, 경과: {post['hours_passed']:.1f}시간")
            if len(yet_posts) > 3:
                print(f"  ... 외 {len(yet_posts) - 3}개")
                
        return {"bad": bad_posts, "yet": yet_posts, "forum_tags": forum_channel.available_tags}
    
    except Exception as e:
        print(f"❌ 오래된 포스트 검색 중 오류 발생: {e}")
        return {"bad": [], "yet": [], "forum_tags": []}

async def convert_yet_to_bad():
    """
    1단계: Yet 태그 포스트를 Bad로 변경하는 함수
    """
    await bot.wait_until_ready()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 1단계: Yet -> Bad 태그 변경 작업 시작")
    print(f"({HOURS_AGO}시간 이상 경과한 Yet 태그 포스트 대상, 포스트 제목 시간 기준)")
    
    while not bot.is_closed():
        converted_count = 0
        
        for server_id in SERVER_CONFIG:
            server_config = SERVER_CONFIG[server_id]
            posts_data = await find_old_posts(server_id)
            
            yet_posts = posts_data["yet"]
            forum_tags = posts_data["forum_tags"]
            
            # Yet 태그 포스트가 있으면 가장 오래된 것부터 Bad로 변경
            if yet_posts:
                oldest_post = yet_posts[0]
                thread = oldest_post["thread"]
                title_time = oldest_post["title_datetime"].strftime('%Y-%m-%d %H:%M')
                hours_passed = oldest_post["hours_passed"]
                
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Yet -> Bad 태그 변경 중: '{thread.name}'")
                print(f"  - 제목 시간: {title_time}")
                print(f"  - 경과 시간: {hours_passed:.1f}시간")
                
                try:
                    alert_channel = bot.get_channel(server_config['detect_channel'])
                    if not alert_channel:
                        alert_channel = await bot.fetch_channel(server_config['detect_channel'])
                    
                    # Yet -> Bad 태그 변경
                    bad_tag = next((tag for tag in forum_tags if tag.id == server_config['tags']['Bad']), None)
                    if bad_tag:
                        print(f"  - 태그 변경 중: Yet -> Bad")
                        await thread.edit(applied_tags=[bad_tag])
                        await alert_channel.send(f"오래된 Yet 포스트를 Bad로 변경: {thread.name} (제목 시간: {title_time}, 경과: {hours_passed:.1f}시간)")
                        print(f"✅ Yet -> Bad 변경 완료: '{thread.name}'")
                        converted_count += 1
                    else:
                        print("❌ Bad 태그를 찾을 수 없습니다.")
                except Exception as e:
                    print(f"❌ Yet 태그 변경 중 오류 발생: {e}")
                
            # 다음 서버로 넘어가기 전에 짧은 대기
            await asyncio.sleep(1)
        
        # 변환된 포스트가 없으면 더 길게 대기
        if converted_count == 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 변환할 Yet 포스트가 없습니다. 300초 대기...")
            await asyncio.sleep(300)  # 5분 대기
        else:
            # 모든 서버 처리 후 DELETE_INTERVAL 만큼 대기
            await asyncio.sleep(DELETE_INTERVAL - 1)  # 위에서 이미 1초씩 기다렸으므로 1초 빼줌

async def delete_bad_posts():
    """
    2단계: Bad 태그 포스트 삭제하는 함수
    """
    await bot.wait_until_ready()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 2단계: Bad 태그 포스트 삭제 작업 시작")
    print(f"({HOURS_AGO}시간 이상 경과한 Bad 태그 포스트 대상, 포스트 제목 시간 기준)")
    
    while not bot.is_closed():
        deleted_count = 0
        
        for server_id in SERVER_CONFIG:
            server_config = SERVER_CONFIG[server_id]
            posts_data = await find_old_posts(server_id)
            
            bad_posts = posts_data["bad"]
            
            # Bad 태그 포스트가 있으면 가장 오래된 것부터 삭제
            if bad_posts:
                oldest_post = bad_posts[0]
                thread = oldest_post["thread"]
                title_time = oldest_post["title_datetime"].strftime('%Y-%m-%d %H:%M')
                hours_passed = oldest_post["hours_passed"]
                
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bad 태그 포스트 삭제 중: '{thread.name}'")
                print(f"  - 제목 시간: {title_time}")
                print(f"  - 경과 시간: {hours_passed:.1f}시간")
                
                try:
                    alert_channel = bot.get_channel(server_config['detect_channel'])
                    if not alert_channel:
                        alert_channel = await bot.fetch_channel(server_config['detect_channel'])
                    
                    await alert_channel.send(f"오래된 Bad 포스트 삭제: {thread.name} (제목 시간: {title_time}, 경과: {hours_passed:.1f}시간)")
                    
                    await thread.delete()
                    print(f"✅ Bad 포스트 삭제 완료: '{thread.name}'")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Bad 스레드 삭제 중 오류 발생: {e}")
            
            # 다음 서버로 넘어가기 전에 짧은 대기
            await asyncio.sleep(1)
        
        # 삭제된 포스트가 없으면 더 길게 대기
        if deleted_count == 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 삭제할 Bad 포스트가 없습니다. 300초 대기...")
            await asyncio.sleep(300)  # 5분 대기
        else:
            # 모든 서버 처리 후 DELETE_INTERVAL 만큼 대기
            await asyncio.sleep(DELETE_INTERVAL - 1)  # 위에서 이미 1초씩 기다렸으므로 1초 빼줌

# 봇 실행
if __name__ == "__main__":
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 오래된 포스트 처리 봇 시작")
        print("-" * 60)
        print("사용 방법:")
        print("1. Yet -> Bad 태그 변경만 하려면 convert_yet_to_bad() 태스크를 활성화")
        print("2. Bad 태그 포스트 삭제만 하려면 delete_bad_posts() 태스크를 활성화")
        print("3. 두 기능 중 하나만 선택해서 사용하세요!")
        print("-" * 60)
        print(f"설정: Group4, Group5 적용, {HOURS_AGO}시간 이상 지난 포스트 처리, 처리 주기: {DELETE_INTERVAL}초")
        print(f"포스트 제목의 시간 정보를 기준으로 경과 시간을 계산합니다.")
        
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"봇 실행 중 오류가 발생했습니다: {e}")