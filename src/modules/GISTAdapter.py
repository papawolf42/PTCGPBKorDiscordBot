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
        """호환성을 위한 메서드"""
        self.load()
        return self.DATA
    
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
        if len(lines) < 3:
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
        name = inform['name']
        number = inform['number']
        pack = inform['pack']
        percent = inform['percent']
        title = f"{name} {number} / {percent:.0f}% / {pack}P / " + time_str
        sub = f"{name} {number} {percent:.0f}% {pack}P"
        save = time_str + ' ' + sub
        
        return title, sub, save
            
    def extract_GodPack(self, lines):
        inform = {}
        
        second_line = lines[1]
        third_line = lines[2]
        
        parts = second_line.split()
        
        pattern = r"([A-Za-z0-9]*[A-Za-z])(\d*)"
        match = re.search(pattern, parts[0])
        if match:
            name, number = match.groups()
            inform['name'] = name
            inform['number'] = number if number else '000'
        else:
            return None
        
        if len(parts) > 1:
            match = re.search(r"\((\d+)\)", parts[1])
            inform['code'] = match.group(1) if match else None
        else:
            inform['code'] = None
            
        pattern = r"(\d+)/(\d+)]\[?(\d+)P\]?"
        match = re.search(pattern, third_line)
        
        if match:
            a, b, p_value = match.groups()
            percentage = (int(a) / int(b)) * 100
            inform['percent'] = percentage
            inform['pack'] = p_value
        else:
            pattern = r"\((\d+)\s+packs\)"
            match = re.search(pattern, third_line)
            if match:
                p_value, = match.groups()
                percentage = 10
                inform['percent'] = percentage
                inform['pack'] = p_value
            else:
                return None
        return inform
    
    def extract_Pseudo(self, lines):
        inform = {'percent': 40 if "Double" in lines[0] else 20}
        
        no_mention = re.sub(r'^.*?found by\s+', '', lines[0])
        
        parts = no_mention.split()
        
        pattern = r"([A-Za-z0-9]*[A-Za-z])(\d*)"
        match = re.search(pattern, parts[0])
        if match:
            name, number = match.groups()
            inform['name'] = name
            inform['number'] = number if number else '000'
        else:
            return None
        
        if len(parts) > 1:
            match = re.search(r"\((\d+)\)", parts[1])
            inform['code'] = match.group(1) if match else None
        else:
            inform['code'] = None
            
        pattern = r"\((\d+) packs.*?\)"
        match = re.search(pattern, lines[0])
        if match:
            inform['pack'] = match.group(1)
        else:
            return None
            
        return inform


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