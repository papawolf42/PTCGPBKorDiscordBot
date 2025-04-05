import discord
import asyncio
import requests
import time
import json
import re
import math
import aiohttp
import io
from discord.ext import commands
from datetime import datetime, timedelta



GITHUB = {'USER' : "os.getenv('GITHUB_USER_ID')", 'TOKEN' : os.getenv('GITHUB_GIST_TOKEN')}

        
class FILE():
    def __init__(self, GIST_ID, GIST_FILE, INITIAL = True):
        self.USER  = GITHUB['USER']
        self.TOKEN = GITHUB['TOKEN']
        self.ID    = GIST_ID
        self.NAME  = GIST_FILE
        self.API   = f"https://api.github.com/gists/{self.ID}"
            
        
    def fetch_url(self):
        api_url = f"https://api.github.com/gists/{self.ID}"
        raw_url = f"https://gist.githubusercontent.com/{self.USER}/{self.ID}/raw/{self.NAME}"
        headers = {"Authorization": f"token {self.TOKEN}"}
        try :
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if self.NAME in data["files"]:
                    return data["files"][self.NAME]["raw_url"]
                else:
                    return raw_url
            else:
                return raw_url
        except :
            return raw_url
        
    def update(self):
        updated = "\n".join(self.DATA)

        headers = {"Authorization": f"token {self.TOKEN}"}
        data = {"files": {self.NAME: {"content": updated}}}
        try:
            response = requests.patch(self.API, json=data, headers=headers)
        except Exception as e:
            print(f"{self.NAME} 에 이상이 있습니다.", e)
        if response.status_code == 200:
            print(f"{self.NAME} 업데이트 명령 보냄!")
        else:
            print(f"{self.NAME} 업데이트 실패: {response.text}")
    
    def fetch(self, URL):
        pass
    
    def fetch_data(self):
        URL = self.fetch_url()
        return self.fetch(URL)
    
    def fetch_raw(self):
        URL = f"https://gist.githubusercontent.com/{self.USER}/{self.ID}/raw/{self.NAME}"
        return self.fetch(URL)
        
    def edit(self):
        pass
    

class TEXT(FILE):
    def __init__(self, GIST_ID, GIST_FILE, INITIAL = True):
        super().__init__(GIST_ID, GIST_FILE)
        if INITIAL :
            self.DATA = self.fetch_data()
        else :
            self.DATA = set()
        
    def fetch(self, URL):
        response = requests.get(URL)
        if response.status_code == 200:
            data = response.text.strip()
            return set(data.splitlines())
        else:
            return set()
            
    def edit(self, MODE, text):
        if MODE == '+' :
            self.DATA.add(text)
        elif MODE == '-' :
            self.DATA.discard(text)
            
            

class JSON(FILE):
    def __init__(self, GIST_ID, GIST_FILE, INITIAL = True):
        super().__init__(GIST_ID, GIST_FILE)
        if INITIAL :
            self.DATA = self.fetch_data()
        else :
            self.DATA = {}
    
    def fetch(self, URL):
        DATA = {}
        response = requests.get(URL)
        if response.status_code == 200:
            data = json.loads(response.text)
            for key, value in data.items() :
                DATA[key] = str(value)
        return DATA
                
    def edit(self, MODE, key, value):
        if MODE == '+' :
            self.DATA[key] = value
        elif MODE == '-' :
            self.DATA.pop(key, None)
            
    def update(self):
        DICT = json.dumps(self.DATA, indent=4, ensure_ascii=False)
        
        headers = {"Authorization": f"token {self.TOKEN}"}
        data = {"files": {self.NAME: {"content": DICT}}}
        try:
            response = requests.patch(self.API, json=data, headers=headers)
        except Exception as e:
            print(f"{self.NAME} 에 이상이 있습니다.", e)
        if response.status_code == 200:
            print(f"{self.NAME} 업데이트 명령 보냄!")
        else:
            print(f"{self.NAME} 업데이트 실패: {response.text}")



class SERVER():
    def __init__(self, ID, File, GodPack, Detect, Posting, Command, Museum, Tag):
        self.ID = ID
        self.FILE = File
        self.GODPACK = GodPack
        self.ONLINE = set()
        self.WAITING = set()
        self.DETECT = Detect
        self.POSTING = Posting
        self.COMMAND = Command
        self.MUSEUM = Museum
        self.Tag = Tag
    
    def found_GodPack(self, message):
        lines = message.content.split("\n")
        if len(lines) < 3 :
            return None, None
        
        inform = self.extract_GodPack(lines)
        
        if not inform :
            return None, None
        
        message_time = message.created_at + timedelta(hours=9)
        formatted_time = message_time.strftime("%Y.%m.%d %H:%M")

        title, sub, save = self.make_title(inform, formatted_time)
        
        duplic = False
        if not inform['code']:
            origin = next((text for text in self.GODPACK.DATA if sub in text), None)
            duplic = origin is not None
        
        if duplic :
            self.GODPACK.edit('+', save, "NaN")
            self.GODPACK.update()
            print("중복 GodPack 입니다")
            return None, None
        else :
            self.GODPACK.edit('+', save, "Yet")
            self.GODPACK.update()
            print("제목 : " + title)
            
        return inform, title
    
    def found_Pseudo(self, message):
        lines = message.content.split("\n")
        if len(lines) < 3 :
            return None, None
        
        inform = self.extract_Pseudo(lines)
        if not inform :
            return None, None
        
        message_time = message.created_at + timedelta(hours=9)
        formatted_time = message_time.strftime("%Y.%m.%d %H:%M")
        
        title, sub, save = self.make_title(inform, formatted_time)
        
        duplic = False
        if not inform['code']:
            origin = next((text for text in self.GODPACK.DATA if sub in text), None)
            duplic = origin is not None
        
        if duplic :
            self.GODPACK.edit('+', save, "NaN")
            self.GODPACK.update()
            print("중복 Pseudo 입니다")
            return None, None
        else :
            self.GODPACK.edit('+', save, "Yet")
            self.GODPACK.update()
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
        if images :
            image_urls = [image.url for image in images if image.content_type.startswith("image")]
            
            image_files = await self.download_images(image_urls)
                
            thread = await forum_channel.create_thread(
                name = title,
                applied_tags = applied_tags,
                files = image_files
            )
        else :
            thread = await forum_channel.create_thread(
                name = title,
                applied_tags = applied_tags,
                content = "No Image"
            )
        
        if thread :
            first_msg = thread.message 
            await first_msg.add_reaction("👎")
            print("포스팅이 완료 되었습니다! 축 기원합니다")
        else :
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
            await channel.send(content = thread.name, files = image_files)
        else :
            raise Exception("이미지가 비어있습니다. 첨부 이미지를 다시 확인하세요.")
    
    
    def make_title(self, inform, time_str):
        name    = inform['name']
        number  = inform['number']
        pack    = inform['pack']
        percent = inform['percent']
        title = f"{name} {number} / {percent:.0f}% / {pack}P / " + time_str
        sub   = f"{name} {number} {percent:.0f}% {pack}P"
        save  = time_str + ' ' + sub
        
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
            inform['name']   = name
            inform['number'] = number if number else '000'
            
        else:
            return None
        
        if len(parts) > 1 :
            match = re.search(r"\((\d+)\)", parts[1])
            inform['code'] = match.group(1) if match else None
        else :
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
            if match :
                p_value, = match.groups()
                percentage = 10
                inform['percent'] = percentage
                inform['pack'] = p_value
            else :
                return None
        return inform
    
    
    def extract_Pseudo(self, lines) :
        inform = {'percent': 40 if "Double" in lines[0] else 20}
        
        no_mention = re.sub(r'^.*?found by\s+', '', lines[0])
        
        parts = no_mention.split()
        
        pattern = r"([A-Za-z0-9]*[A-Za-z])(\d*)"
        match = re.search(pattern, parts[0])
        if match:
            name, number = match.groups()
            inform['name'] = name
            inform['number'] = number if number else '000'
        else :
            return None
        
        if len(parts) > 1 :
            match = re.search(r"\((\d+)\)", parts[1])
            inform['code'] = match.group(1) if match else None
        else :
            inform['code'] = None
            
        pattern = r"\((\d+) packs.*?\)"
        match = re.search(pattern, lines[0])
        if match :
            inform['pack'] = match.group(1)
        else :
            return None
            
        return inform
        


class USER():
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
            return max(self.off.values(), key = lambda x : x['TIME'])['TIME']
        else :
            return None
        
    def extract(self, message):
        inform = {'TIME' : message.created_at}
        lines = message.content.split("\n")
        for line in lines:
            if 'Online' in line:
                numbers = re.findall(r'\d+', line)
                inform['BARRACKS'] =  len(numbers)
                
            if 'Time' in line:
                pattern = r"Time:\s*(\d+)m\s+Packs:\s*(\d+)\s*\|\s*Avg:\s*([\d.]+)\s*packs/min"
                match = re.search(pattern, line)
                if match:
                    inform['RUNTIME'] = int(match.group(1))
                    inform['PACKS']   = int(match.group(2))
                    if inform['RUNTIME'] :
                        inform['AVG'] = float(match.group(3))
                    else :
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
                    
                    
        return inform


