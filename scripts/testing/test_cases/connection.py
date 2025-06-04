"""
connection.py - 연결 관련 테스트 케이스
봇 시작, 클라이언트 연결, 채널 접근 등의 초기화 테스트
"""

import asyncio
import subprocess
from pathlib import Path
from .base import BaseTestCase


class ConnectionTests(BaseTestCase):
    """연결 관련 테스트 케이스"""
    
    async def test_bot_startup(self):
        """Poke.py 봇 프로세스 시작 테스트"""
        # 환경 변수 설정
        import os
        env = os.environ.copy()
        env['TEST_MODE'] = 'true'
        env['TEST_DURATION'] = '300'  # 5분
        
        # 봇 프로세스 시작
        self.simulator.bot_process = subprocess.Popen(
            ['python', '-m', 'src.bots.Poke'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # 봇 로그 모니터링 시작
        self.simulator.bot_log_task = asyncio.create_task(
            self.simulator.monitor_bot_logs()
        )
        
        # 봇 시작 확인 (최대 10초 대기)
        for i in range(10):
            # 프로세스가 종료되었는지 확인
            if self.simulator.bot_process.poll() is not None:
                return self.format_result(
                    False,
                    '봇 프로세스가 즉시 종료됨',
                    {'returncode': self.simulator.bot_process.returncode}
                )
            
            # 로그에서 로그인 확인
            if self.check_recent_bot_logs("로그인됨", limit=50):
                return self.format_result(
                    True,
                    '봇 시작 및 로그인 성공'
                )
            
            await asyncio.sleep(1)
        
        return self.format_result(
            False,
            '봇 시작 시간 초과'
        )
    
    async def test_client_connect(self):
        """테스트 클라이언트 Discord 연결"""
        import discord
        
        # Discord 클라이언트 설정
        intents = discord.Intents.default()
        intents.message_content = True
        self.simulator.test_client = discord.Client(intents=intents)
        
        # 연결 이벤트 설정
        connected = asyncio.Event()
        
        @self.simulator.test_client.event
        async def on_ready():
            connected.set()
        
        # 비동기로 클라이언트 시작
        asyncio.create_task(
            self.simulator.test_client.start(self.simulator.token)
        )
        
        # 연결 대기 (최대 10초)
        try:
            await asyncio.wait_for(connected.wait(), timeout=10.0)
            return self.format_result(
                True,
                f'테스트 클라이언트 연결 성공: {self.simulator.test_client.user}'
            )
        except asyncio.TimeoutError:
            return self.format_result(
                False,
                '테스트 클라이언트 연결 시간 초과'
            )
    
    async def test_channel_access(self):
        """채널 접근 권한 확인"""
        accessible = {}
        
        # 각 채널에 대해 접근 확인
        for name, channel_id in self.simulator.channel_ids.items():
            if channel_id:
                channel = self.simulator.test_client.get_channel(channel_id)
                if channel:
                    self.simulator.channels[name] = channel
                    accessible[name] = True
                    
                    # 채널 권한 확인
                    try:
                        permissions = channel.permissions_for(channel.guild.me)
                        can_send = permissions.send_messages
                        can_read = permissions.read_messages
                        accessible[f"{name}_permissions"] = {
                            'can_send': can_send,
                            'can_read': can_read
                        }
                    except:
                        pass
                else:
                    accessible[name] = False
            else:
                accessible[name] = False
        
        # 최소 2개 채널 접근 가능해야 성공
        accessible_count = sum(1 for k, v in accessible.items() 
                             if isinstance(v, bool) and v)
        success = accessible_count >= 2
        
        return self.format_result(
            success,
            f"채널 접근: {accessible_count}/{len(self.simulator.channel_ids)} 성공",
            accessible
        )
    
    async def test_data_directory(self):
        """테스트 데이터 디렉토리 확인"""
        data_path = self.test_data_path
        poke_data_path = data_path / 'poke_data'
        
        # 디렉토리 존재 확인
        exists = {
            'data_test': data_path.exists(),
            'poke_data': poke_data_path.exists(),
            'group7': (poke_data_path / 'group7').exists(),
            'group8': (poke_data_path / 'group8').exists(),
            'common': (poke_data_path / 'common').exists()
        }
        
        # 쓰기 권한 확인
        try:
            test_file = data_path / 'test_write.tmp'
            test_file.write_text('test')
            test_file.unlink()
            can_write = True
        except:
            can_write = False
        
        success = all(exists.values()) and can_write
        
        return self.format_result(
            success,
            '테스트 데이터 디렉토리 준비 완료' if success else '데이터 디렉토리 문제 발견',
            {
                'directories': exists,
                'writable': can_write
            }
        )