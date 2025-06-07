"""
GISTAdapter.py - GIST 인터페이스를 유지하면서 LocalFile을 사용하는 어댑터
기존 Poke.py 코드를 최소한으로 수정하면서 로컬 파일 시스템을 사용할 수 있도록 합니다.
"""

import os
import json
import re
import discord
import aiohttp
import io
from datetime import datetime, timedelta
from .LocalFile import LocalFile
from .paths import get_data_path

class GISTAdapter:
    """GIST 클래스와 동일한 인터페이스를 제공하는 어댑터"""
    
    def __init__(self):
        # TEST_MODE 확인
        import os
        is_test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        
        # TEST_MODE일 때는 data_test 사용
        if is_test_mode:
            from .paths import TEST_DATA_DIR
            base_path = os.path.join(TEST_DATA_DIR, "poke_data")
        else:
            base_path = get_data_path("poke_data")
            
        # LocalFile 인스턴스 생성
        self.local_storage = LocalFile(base_path=base_path)
    
    def TEXT(self, gist_id, filename, initial=True):
        """GIST.TEXT와 동일한 인터페이스"""
        # 파일명에서 그룹/타입 매핑
        mapping = {
            "Admin": ("common", "admin.txt"),
            "Group7": ("group7", "online.txt"),
            "Group8": ("group8", "online.txt"),
            # TEST_MODE 매핑
            "GroupTest": ("test", "online.txt"),
        }
        
        folder, local_filename = mapping.get(filename, ("common", f"{filename}.txt"))
        return TextAdapter(self.local_storage, folder, local_filename, name=filename, initial=initial)
    
    def JSON(self, gist_id, filename):
        """GIST.JSON과 동일한 인터페이스"""
        # 파일명에서 그룹/타입 매핑
        mapping = {
            "Alliance": ("common", "member.json"),
            "GodPack7": ("group7", "godpack.json"),
            "Code7": ("group7", "godpackCode.json"),
            "GodPack8": ("group8", "godpack.json"),
            "Code8": ("group8", "godpackCode.json"),
            # TEST_MODE 매핑
            "GodPackTest": ("test", "godpack.json"),
            "CodeTest": ("test", "godpackCode.json"),
        }
        
        folder, local_filename = mapping.get(filename, ("common", f"{filename}.json"))
        return JsonAdapter(self.local_storage, folder, local_filename, name=filename)
    
    def SERVER(self, *args):
        """GIST.SERVER와 동일한 인터페이스"""
        # GIST 모듈의 SERVER 클래스 import
        from .GIST import SERVER
        return SERVER(*args)
    
    def USER(self, *args):
        """GIST.USER와 동일한 인터페이스"""
        # GIST 모듈의 USER 클래스 import
        from .GIST import USER
        return USER(*args)


class TextAdapter:
    """GIST TEXT 클래스 어댑터"""
    
    def __init__(self, storage, folder, filename, name=None, initial=True):
        self.storage = storage
        self.folder = folder
        self.filename = filename
        self.file_path = os.path.join(storage.base_path, folder, filename)
        self.DATA = set()
        self.NAME = name  # GIST와의 호환성을 위해 추가
        # GIST와 동일한 동작: initial=True일 때만 파일 로드
        if initial:
            self.load()
        # initial=False면 빈 set으로 시작
    
    def load(self):
        """파일에서 데이터 로드"""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    self.DATA = set(content.split('\n'))
                else:
                    self.DATA = set()
        else:
            self.DATA = set()
    
    def update(self):
        """변경사항을 파일에 저장"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(self.DATA)))
        return True
    
    def edit(self, mode, text):
        """데이터 편집"""
        if mode == '+':
            self.DATA.add(text)
        elif mode == '-':
            self.DATA.discard(text)
    
    def fetch_raw(self):
        """호환성을 위한 메서드 - GIST 동작 모방"""
        # GIST는 항상 최신 데이터를 GitHub에서 가져오므로
        # 여기서도 파일에서 직접 읽어서 반환
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        return set()
    
    def fetch_data(self):
        """호환성을 위한 메서드"""
        self.load()
        return self.DATA


class JsonAdapter:
    """GIST JSON 클래스 어댑터"""
    
    def __init__(self, storage, folder, filename, name=None):
        self.storage = storage
        self.folder = folder
        self.filename = filename
        self.file_path = os.path.join(storage.base_path, folder, filename)
        self.DATA = {}
        self.NAME = name  # GIST와의 호환성을 위해 추가
        self.load()
    
    def load(self):
        """파일에서 데이터 로드"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.DATA = json.load(f)
            except json.JSONDecodeError:
                self.DATA = {}
        else:
            self.DATA = {}
    
    def update(self):
        """변경사항을 파일에 저장"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.DATA, f, ensure_ascii=False, indent=2)
        return True
    
    def edit(self, mode, key, value=None):
        """데이터 편집"""
        if mode == '+':
            self.DATA[key] = value
        elif mode == '-':
            self.DATA.pop(key, None)
    
    def fetch_raw(self):
        """호환성을 위한 메서드"""
        self.load()
        return self.DATA
    
    def fetch_data(self):
        """호환성을 위한 메서드"""
        self.load()
        return self.DATA


# SERVER 클래스 (GIST.py와 동일)
class SERVER:
    def __init__(self, ID, File, GodPack, GPTest, Detect, Posting, Command, Museum, Tag):
        self.ID = ID
        self.FILE = File
        self.GODPACK = GodPack
        self.GPTEST = GPTest
        self.ONLINE = set()
        self.WAITING = set()
        self.DETECT = Detect
        self.POSTING = Posting
        self.COMMAND = Command
        self.MUSEUM = Museum
        self.Tag = Tag
    
    def found_GodPack(self, message):
        lines = message.content.split("\n")
        if len(lines) < 3:
            return None, None
        
        inform = self.extract_GodPack(lines)
        
        if not inform:
            return None, None
        
        message_time = message.created_at + timedelta(hours=9)
        formatted_time = message_time.strftime("%Y.%m.%d %H:%M")

        title, sub, save = self.make_title(inform, formatted_time)
        
        duplic = False
        if not inform['code']:
            origin = next((text for text in self.GODPACK.DATA if sub in text), None)
            duplic = origin is not None
        
        if duplic:
            self.GODPACK.edit('+', save, "NaN")
            self.GODPACK.update()
            print("중복 GodPack 입니다")
            return None, None
        else:
            self.GODPACK.edit('+', save, "Yet")
            self.GODPACK.update()
            if inform['code']:
                self.GPTEST.edit('+', save, inform['code'])
            else:
                self.GPTEST.edit('+', save, 'NaN')
            self.GPTEST.update()
            print("제목 : " + title)
            
        return inform, title
    
    def found_Pseudo(self, message):
        lines = message.content.split("\n")
        
        # Double two star 등 1줄 메시지를 위한 예외 처리
        if len(lines) == 1 and "found by" in lines[0]:
            # 1줄 메시지도 처리 가능
            pass
        elif len(lines) < 3:
            # 기존 3줄 이상 필요한 메시지들을 위한 체크
            return None, None
        
        inform = self.extract_Pseudo(lines)
        if not inform:
            return None, None
        
        message_time = message.created_at + timedelta(hours=9)
        formatted_time = message_time.strftime("%Y.%m.%d %H:%M")
        
        title, sub, save = self.make_title(inform, formatted_time)
        
        duplic = False
        if not inform['code']:
            origin = next((text for text in self.GODPACK.DATA if sub in text), None)
            duplic = origin is not None
        
        if duplic:
            self.GODPACK.edit('+', save, "NaN")
            self.GODPACK.update()
            print("중복 Pseudo 입니다")
            return None, None
        else:
            self.GODPACK.edit('+', save, "Yet")
            self.GODPACK.update()
            if inform['code']:
                self.GPTEST.edit('+', save, inform['code'])
            else:
                self.GPTEST.edit('+', save, 'NaN')
            self.GPTEST.update()
            print("제목 : " + title)
            
        return inform, title
    
    async def Post(self, forum_channel, images, inform, title):
        applied_tags = []
        forum_tags = forum_channel.available_tags
        base_tag = next((tag for tag in forum_tags if tag.id == self.Tag['Yet']), None)
        if base_tag:
            applied_tags.append(base_tag)

        p_tag = str(inform['pack']) + "P"
        if p_tag in self.Tag:
            p_tag_id = self.Tag[p_tag]
            p_tag = next((tag for tag in forum_tags if tag.id == p_tag_id), None)
            if p_tag:
                applied_tags.append(p_tag)
        if images:
            image_urls = [image.url for image in images if image.content_type.startswith("image")]
            
            image_files = await self.download_images(image_urls)
                
            thread = await forum_channel.create_thread(
                name=title,
                applied_tags=applied_tags,
                files=image_files
            )
        else:
            thread = await forum_channel.create_thread(
                name=title,
                applied_tags=applied_tags,
                content="No Image"
            )
        
        if thread:
            first_msg = thread.message 
            await first_msg.add_reaction("👎")
            print("포스팅이 완료 되었습니다! 축 기원합니다")
        else:
            print("포스팅에 실패")
            
    async def download_images(self, image_urls):
        image_files = []
        async with aiohttp.ClientSession() as session:
            for url in image_urls:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        image_files.append(discord.File(fp=io.BytesIO(image_data), filename="image.png"))
        return image_files
    
    async def post_museum(self, thread, channel):
        first_msg = await thread.fetch_message(thread.id)
        images = first_msg.attachments
        image_urls = [image.url for image in images if image.content_type.startswith("image")]
        image_files = await self.download_images(image_urls)
        
        if image_files:
            await channel.send(content=thread.name, files=image_files)
        else:
            raise Exception("이미지가 비어있습니다. 첨부 이미지를 다시 확인하세요.")
    
    def make_title(self, inform, time_str):
        name = inform['name']        # 사용자명
        number = inform['number']    # 팩 종류 (Solgaleo, Palkia 등)
        pack = inform['pack']        # 팩 순서 (1~5)
        percent = inform['percent']  # 갓팩: 2성 비율(20~100), Special: 카드 타입(Trainer 등)
        
        # 팩 타입에 따라 다른 형식 사용
        if inform['type'] == 'godpack':
            # 갓팩 형식: "DUCK Solgaleo / 100% / 3P / 시간"
            percent_val = float(percent) if isinstance(percent, str) else percent
            title = f"{name} {number} / {percent_val:.0f}% / {pack}P / " + time_str
            sub = f"{name} {number} {percent_val:.0f}% {pack}P"
        elif inform['type'] == 'special':
            # Special Card 형식: "User Palkia / Trainer / 1P / 시간"
            title = f"{name} {number} / {percent} / {pack}P / " + time_str
            sub = f"{name} {number} {percent} {pack}P"
        else:
            # 예외 처리 (있을 경우)
            print(f"[GISTAdapter] make_title: 알 수 없는 타입 - {inform.get('type')}")
            return None, None, None
        
        save = time_str + ' ' + sub
        
        return title, sub, save
            
    def extract_GodPack(self, lines):
        pattern = re.compile(r"\[(\d)/5\]\[(\d+)P\]\[(\w+)\]")
        pattern2 = re.compile(r"^(.*?)\s*\((.*?)\)$")

        # lines 길이 체크
        if len(lines) < 2:
            print(f"[GISTAdapter] extract_GodPack: 라인 수 부족 (최소 2줄 필요, 현재 {len(lines)}줄)")
            return None

        for line in lines:
            match = pattern.search(line)
            if match:
                percent = str(int(match.group(1)) * 20)  # 2성 비율
                pack = match.group(2)                     # 팩 순서  
                number = match.group(3)                   # 팩 종류
                
                # 두 번째 라인에서 이름과 코드 추출
                match2 = pattern2.search(lines[1])
                if match2:
                    name = match2.group(1).strip()       # 사용자명
                    code = match2.group(2)               # 친구코드
                    
                    # inform 딕셔너리 - 실제 의미:
                    # name: 사용자명 (예: DUCK, Saisai2)
                    # number: 팩 종류 (예: Solgaleo, Palkia, Buzzwole)
                    # percent: 2성 이상 카드 비율 (20/40/60/80/100)
                    # pack: 팩 순서 (1~5번째 중 몇 번째 팩에서 나왔는지)
                    # code: 16자리 친구코드
                    inform = {
                        "name": name,
                        "number": number,    # 팩 종류
                        "percent": percent,  # 2성 비율
                        "pack": pack,        # 팩 순서
                        "code": code
                    }
                    inform['type'] = 'godpack'  # 파싱 성공 시 타입 추가
                    print(f"[GISTAdapter] extract_GodPack: 파싱 성공 - {percent}%, {name}, {number}")
                    return inform

        print(f"[GISTAdapter] extract_GodPack: 파싱 실패")
        return None
    
    def extract_Pseudo(self, lines):
        # "Special Card" 메시지 포맷을 분석하는 정규식
        # 예: "Trainer found by User (123...)" 또는 "Double two star found by User (123...)"
        pattern = re.compile(r"(.+?) found by (.*?) \((\d{16})\) in instance: \d+ \((\d+) packs, ([^)]+)\)")

        for line in lines:
            # 라인 시작 부분의 @멘션 (e.g., @Rami) 을 먼저 제거하여 정규식에 방해되지 않도록 함
            cleaned_line = re.sub(r'^@\S+\s*', '', line.strip())
            
            match = pattern.search(cleaned_line)
            if match:
                star_type = match.group(1).strip()     # 카드 타입
                name = match.group(2).strip()          # 사용자명
                friend_code = match.group(3)           # 친구코드
                pack_count = match.group(4)            # 팩 순서
                card_name = match.group(5).strip()     # 팩 종류

                # inform 딕셔너리 - 실제 의미:
                # name: 사용자명 (예: 「NEQI ㆍ귀이이 1.•넅)
                # number: 팩 종류 (예: Palkia, Solgaleo)
                # percent: 카드 타입 (Trainer/Full Art/Rainbow/Double two star)
                # pack: 팩 순서 (1~5번째 중 몇 번째 팩에서 나왔는지)
                # code: 16자리 친구코드
                inform = {
                    "name": name,
                    "number": card_name,    # 팩 종류
                    "percent": star_type,   # Special Card에서는 카드 타입
                    "pack": pack_count,     # 팩 순서
                    "code": friend_code
                }
                inform['type'] = 'special'  # 파싱 성공 시 타입 추가
                print(f"[GISTAdapter] extract_Pseudo: 파싱 성공 - {star_type}, {name}, {card_name}")
                return inform
            else:
                # 디버깅을 위한 로그
                if "found by" in cleaned_line:
                    print(f"[GISTAdapter] extract_Pseudo: 파싱 실패 - {cleaned_line[:50]}...")

        return None


# USER 클래스 (GIST.py와 동일)
class USER:
    def __init__(self, NAME, CODE):
        self.NAME = NAME
        self.CODE = CODE
        self.Server = set()
        self.inform = {}
        self.off = {}
        
    def __eq__(self, other):
        return isinstance(other, USER) and self.CODE == other.CODE

    def __hash__(self):
        return hash(self.CODE)
    
    def called(self, Server, message):
        self.Server.add(Server)
        self.inform[Server.ID] = self.extract(message)
    
    def onlined(self, Server):
        Server.FILE.edit('+', self.CODE)
        Server.ONLINE.add(self)
    
    def online(self, Server):
        Server.FILE.edit('+', self.CODE)
        Server.WAITING.add(self)
    
    def offlined(self, Server, message):
        self.off[Server.ID] = self.extract(message)
    
    def offline(self, Server):
        self.Server.discard(Server)
        Server.FILE.edit('-', self.CODE)
        Server.ONLINE.discard(self)
        self.off[Server.ID] = self.inform[Server.ID].copy()
    
    def lastoff(self):
        if self.off:
            return max(self.off.values(), key=lambda x: x['TIME'])['TIME']
        else:
            return None
        
    def extract(self, message):
        inform = {'TIME': message.created_at}
        lines = message.content.split("\n")
        for line in lines:
            if 'Online' in line:
                numbers = re.findall(r'\d+', line)
                inform['BARRACKS'] = len(numbers)
                
            if 'Time' in line:
                pattern = r'Time:\s*(\d+)m.*?Packs:\s*(\d+).*?Avg:\s*([\d.]+)'
                match = re.search(pattern, line)
                if match:
                    inform['RUNTIME'] = int(match.group(1))
                    inform['PACKS'] = int(match.group(2))
                    if inform['RUNTIME']:
                        inform['AVG'] = float(match.group(3))
                    else:
                        inform['AVG'] = float('nan')
                    
            if 'Type' in line:
                num_pattern = r"Type:\s*(\d+)"
                num_match = re.search(num_pattern, line)
                inform['TYPE'] = int(num_match.group(1)) if num_match else None
                
                bracket_pattern = r"\(([^)]+)\)"
                inform['METHOD'] = re.findall(bracket_pattern, line)
                
            if 'Select' in line:
                match = re.search(r"Select:\s*(.*)", line)
                if match:
                    content = match.group(1)
                    inform['SELECT'] = [item.strip() for item in content.split(',') if item.strip()]
                    
            if 'Opening' in line:
                match = re.search(r"Opening:\s*(.*)", line)
                if match:
                    content = match.group(1)
                    inform['SELECT'] = [item.strip() for item in content.split(',') if item.strip()]
                    
        return inform


# 싱글톤 인스턴스
_adapter = GISTAdapter()

# GIST 모듈과 동일한 인터페이스 제공
TEXT = _adapter.TEXT
JSON = _adapter.JSON
SERVER = SERVER  # 클래스 직접 참조
USER = USER      # 클래스 직접 참조