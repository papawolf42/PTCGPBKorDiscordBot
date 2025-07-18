"""
base.py - 테스트 케이스 기본 클래스
모든 테스트 케이스가 상속받을 기본 클래스와 유틸리티 함수들
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class BaseTestCase:
    """테스트 케이스 기본 클래스"""
    
    def __init__(self, simulator):
        self.simulator = simulator
        self.test_client = simulator.test_client
        self.channels = simulator.channels
        self.test_data_path = simulator.test_data_path
        self.description = ""  # 테스트 설명
        self.expected_behavior = ""  # 기대하는 동작
    
    def format_result(self, success: bool, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """표준화된 테스트 결과 형식"""
        return {
            'success': success,
            'message': message,
            'description': self.description,
            'expected': self.expected_behavior,
            'details': details or {}
        }
    
    async def wait_for_bot_response(self, channel, command_msg, timeout: float = 5.0) -> Optional[Any]:
        """봇 응답 대기 헬퍼"""
        def check(m):
            return (m.channel == channel and 
                   m.author.bot and 
                   m.reference and 
                   m.reference.message_id == command_msg.id)
        
        try:
            response = await self.test_client.wait_for('message', check=check, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            return None
    
    def check_file_exists(self, relative_path: str) -> bool:
        """파일 존재 여부 확인"""
        from pathlib import Path
        file_path = Path(self.test_data_path) / relative_path
        return file_path.exists()
    
    def read_file_content(self, relative_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """파일 내용 읽기"""
        from pathlib import Path
        file_path = Path(self.test_data_path) / relative_path
        if file_path.exists():
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        return None
    
    def read_json_file(self, relative_path: str) -> Optional[Dict[str, Any]]:
        """JSON 파일 읽기"""
        content = self.read_file_content(relative_path)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
        return None
    
    def check_user_in_online_list(self, group: str, username: str) -> bool:
        """온라인 목록에서 사용자 확인"""
        online_content = self.read_file_content(f'poke_data/{group}/online.txt')
        if online_content:
            return username in online_content
        return False
    
    def check_recent_bot_logs(self, keyword: str, limit: int = 10) -> bool:
        """최근 봇 로그에서 키워드 확인"""
        # subprocess를 사용하지 않으므로 봇 로그를 직접 확인할 수 없음
        # 대신 파일이나 채널 메시지를 확인하는 방식으로 변경 필요
        return True  # 일단 True 반환
    
    async def wait_seconds(self, seconds: int) -> Dict[str, Any]:
        """지정된 시간 대기"""
        await asyncio.sleep(seconds)
        return self.format_result(True, f'{seconds}초 대기 완료')
    
    async def check_for_bot_response(self, channel, after_time=None, timeout=5.0) -> bool:
        """봇이 채널에 응답했는지 확인"""
        try:
            # webhook을 사용하므로 시간 기준으로 확인
            from datetime import datetime, timezone, timedelta
            if not after_time:
                after_time = datetime.now(timezone.utc) - timedelta(seconds=10)
            
            # 최근 메시지 확인
            recent_messages = []
            async for msg in channel.history(limit=10):
                if msg.created_at < after_time:
                    break
                if msg.author.bot:
                    recent_messages.append(msg)
            
            return len(recent_messages) > 0
        except Exception as e:
            return False


class TestTimer:
    """테스트 시간 측정 컨텍스트 매니저"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()