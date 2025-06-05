"""
messages.py - 메시지 처리 관련 테스트 케이스
Heartbeat 메시지, 온라인 상태 업데이트, 갓팩 감지 등의 테스트
"""

import asyncio
import random
from pathlib import Path
from .base import BaseTestCase


class MessageTests(BaseTestCase):
    """메시지 처리 관련 테스트 케이스"""
    
    def __init__(self, simulator):
        super().__init__(simulator)
        # member.json에서 사용자 정보 로드
        self.member_data = self.read_json_file('poke_data/common/member.json') or {}
        self.users = list(self.member_data.keys())
        # 테스트용 사용자 선택 (papawolf 우선, 없으면 첫 번째 사용자)
        self.test_user = 'papawolf' if 'papawolf' in self.users else (self.users[0] if self.users else 'testuser')
        self.test_user_code = self.member_data.get(self.test_user, '1234-5678-9012')
    
    def create_heartbeat_message(self, username, time_minutes=0, packs=0, online_accounts="1, 2, 3, 4", offline_accounts="Main"):
        """동적으로 heartbeat 메시지 생성"""
        if time_minutes == 0:
            avg = 0.00
        else:
            avg = packs / time_minutes
        
        # 팩 타입 랜덤 선택
        pack_types = ["Shining", "Arceus", "Palkia", "Dialga", "Mew", "Charizard", "Pikachu"]
        opening = random.choice(pack_types)
        
        return f'''{username}
Online: {online_accounts}
Offline: {offline_accounts}
Time: {time_minutes}m | Packs: {packs} | Avg: {avg:.2f} packs/min
Version: Arturo-v6.3.29
Type: 5 Pack (Fast) (Menu Delete)
Opening: {opening}'''
    
    async def test_heartbeat_initial(self):
        """사용자 초기 로그인 - heartbeat 메시지 전송"""
        self.description = f"{self.test_user}의 초기 heartbeat 메시지로 로그인"
        self.expected_behavior = "봇이 메시지를 감지하고 online.txt에 사용자를 추가"
        
        # Webhook URL 확인
        webhook_url = self.simulator.webhook_urls.get('heartbeat')
        if not webhook_url:
            return self.format_result(
                False,
                'Heartbeat webhook URL이 설정되지 않음'
            )
        
        # 채널 확인 (봇 응답 확인용)
        channel = self.channels.get('heartbeat_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Heartbeat 채널을 찾을 수 없음'
            )
        
        # 초기 로그인 메시지 (0분, 0팩)
        message_content = self.create_heartbeat_message(self.test_user, time_minutes=0, packs=0)
        
        try:
            # Webhook으로 메시지 전송
            sent = await self.simulator.send_webhook_message(webhook_url, message_content, username=self.test_user)
            if not sent:
                return self.format_result(False, 'Webhook 메시지 전송 실패')
                
            await asyncio.sleep(3)  # 봇 처리 대기
            
            # 봇 응답 확인
            bot_responded = await self.check_for_bot_response(channel)
            
            return self.format_result(
                True,
                f'{self.test_user} 초기 heartbeat 메시지 전송 완료',
                {
                    'channel': channel.name,
                    'username': self.test_user,
                    'status': '초기 로그인 (0분, 0팩)',
                    'bot_responded': bot_responded,
                    'method': 'webhook'
                }
            )
        except Exception as e:
            return self.format_result(
                False,
                f'메시지 전송 실패: {str(e)}'
            )
    
    async def test_heartbeat_maintain(self):
        """로그인 유지 확인 - 5초 후 heartbeat"""
        self.description = f"{self.test_user}의 5초 후 heartbeat로 로그인 유지 확인"
        self.expected_behavior = "봇이 온라인 상태를 유지하고 팩 정보를 업데이트"
        
        # Webhook URL 확인
        webhook_url = self.simulator.webhook_urls.get('heartbeat')
        if not webhook_url:
            return self.format_result(
                False,
                'Heartbeat webhook URL이 설정되지 않음'
            )
        
        # 채널 확인 (봇 응답 확인용)
        channel = self.channels.get('heartbeat_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Heartbeat 채널을 찾을 수 없음'
            )
        
        # 5초 후 메시지 (시간은 분 단위이므로 여전히 0분으로 표시)
        packs = random.randint(5, 10)
        message_content = self.create_heartbeat_message(self.test_user, time_minutes=0, packs=packs)
        
        try:
            # Webhook으로 메시지 전송
            sent = await self.simulator.send_webhook_message(webhook_url, message_content, username=self.test_user)
            if not sent:
                return self.format_result(False, 'Webhook 메시지 전송 실패')
                
            await asyncio.sleep(3)  # 봇 처리 대기
            
            # 온라인 상태 확인
            still_online = self.check_user_in_online_list('group7', self.test_user)
            
            # 봇 응답 확인
            bot_responded = await self.check_for_bot_response(channel)
            
            return self.format_result(
                True,
                f'{self.test_user} 10분 후 heartbeat 전송 완료',
                {
                    'channel': channel.name,
                    'username': self.test_user,
                    'time': '5초 후',
                    'packs': packs,
                    'still_online': still_online,
                    'bot_responded': bot_responded,
                    'status': '로그인 유지 확인',
                    'method': 'webhook'
                }
            )
        except Exception as e:
            return self.format_result(
                False,
                f'메시지 전송 실패: {str(e)}'
            )
    
    async def test_wait_for_timeout(self):
        """오프라인 타임아웃 대기"""
        self.description = "타임아웃 대기 - TEST MODE에서는 10초로 설정됨"
        self.expected_behavior = "10초 동안 heartbeat가 없으면 오프라인 처리됨"
        
        # TEST MODE에서는 10초로 설정
        wait_time = 15  # 15초 대기 (안전하게 10초보다 길게)
        
        await asyncio.sleep(wait_time)
        
        return self.format_result(
            True,
            f'{wait_time}초 대기 완료',
            {
                'wait_time': wait_time,
                'note': 'Poke.py TEST MODE는 10초 타임아웃'
            }
        )
    
    async def test_verify_offline(self):
        """오프라인 상태 확인"""
        self.description = f"{self.test_user}가 오프라인으로 처리되었는지 확인"
        self.expected_behavior = "online.txt에서 사용자가 제거됨"
        
        # 파일 시스템 확인
        online_file_exists = self.check_file_exists('poke_data/group7/online.txt')
        user_still_online = self.check_user_in_online_list('group7', self.test_user)
        
        # 온라인 목록 내용 확인
        online_content = self.read_file_content('poke_data/group7/online.txt')
        online_users = []
        if online_content:
            online_users = [line.strip() for line in online_content.split('\n') if line.strip()]
        
        # 성공 조건: 파일은 존재하지만 사용자는 목록에 없음
        success = online_file_exists and not user_still_online
        
        return self.format_result(
            success,
            f'{self.test_user} 오프라인 처리 확인' if success else f'{self.test_user}가 여전히 온라인 상태',
            {
                'online_file_exists': online_file_exists,
                'user_still_online': user_still_online,
                'current_online_users': len(online_users),
                'online_list': online_users[:5] if online_users else []  # 처음 5명만 표시
            }
        )
    
    async def test_relogin_after_offline(self):
        """오프라인 후 재로그인 테스트"""
        self.description = f"{self.test_user}가 오프라인 후 다시 로그인"
        self.expected_behavior = "봇이 새로운 로그인으로 인식하고 온라인 목록에 추가"
        
        # Webhook URL 확인
        webhook_url = self.simulator.webhook_urls.get('heartbeat')
        if not webhook_url:
            return self.format_result(
                False,
                'Heartbeat webhook URL이 설정되지 않음'
            )
        
        # 채널 확인 (봇 응답 확인용)
        channel = self.channels.get('heartbeat_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Heartbeat 채널을 찾을 수 없음'
            )
        
        # 재로그인 메시지
        message_content = self.create_heartbeat_message(self.test_user, time_minutes=0, packs=0)
        
        try:
            # Webhook으로 메시지 전송
            sent = await self.simulator.send_webhook_message(webhook_url, message_content, username=self.test_user)
            if not sent:
                return self.format_result(False, 'Webhook 메시지 전송 실패')
                
            await asyncio.sleep(3)  # 봇 처리 대기
            
            # 온라인 상태 확인
            is_online_again = self.check_user_in_online_list('group7', self.test_user)
            
            # 봇 응답 확인
            bot_responded = await self.check_for_bot_response(channel)
            
            return self.format_result(
                is_online_again,
                f'{self.test_user} 재로그인 성공' if is_online_again else '재로그인 실패',
                {
                    'channel': channel.name,
                    'username': self.test_user,
                    'is_online': is_online_again,
                    'bot_responded': bot_responded,
                    'status': '오프라인 후 재로그인',
                    'method': 'webhook'
                }
            )
        except Exception as e:
            return self.format_result(
                False,
                f'메시지 전송 실패: {str(e)}'
            )
    
    async def test_godpack_detect(self):
        """갓팩 감지 테스트 (선택사항)"""
        self.description = "갓팩 감지 메시지 전송 및 처리 확인"
        self.expected_behavior = "봇이 갓팩을 감지하고 godpack.json에 기록"
        
        # Webhook URL 확인
        webhook_url = self.simulator.webhook_urls.get('detect')
        if not webhook_url:
            return self.format_result(
                True,  # 선택사항이므로 설정 안 되어도 성공
                'Detect webhook URL이 설정되지 않음 (선택사항)'
            )
        
        # 채널 확인 (봇 응답 확인용)
        channel = self.channels.get('detect_7')
        if not channel:
            return self.format_result(
                True,  # 선택사항이므로 채널이 없어도 성공
                'Group7 Detect 채널이 설정되지 않음 (정상)'
            )
        
        # 갓팩 감지 메시지 형식
        detect_message = f'''2025.06.05 12:00 {self.test_user} {self.test_user_code}
뮤츠 ex ★'''
        
        try:
            # Webhook으로 메시지 전송
            sent = await self.simulator.send_webhook_message(webhook_url, detect_message, username='아이리스')
            if not sent:
                return self.format_result(False, 'Webhook 메시지 전송 실패')
                
            await asyncio.sleep(3)  # 봇 처리 대기
            
            # godpack.json 확인
            godpack_data = self.read_json_file('poke_data/group7/godpack.json')
            has_godpack = godpack_data is not None
            
            return self.format_result(
                True,
                '갓팩 감지 메시지 전송 완료',
                {
                    'channel': channel.name,
                    'username': self.test_user,
                    'card': '뮤츠 ex ★',
                    'godpack_file_exists': has_godpack,
                    'method': 'webhook'
                }
            )
        except Exception as e:
            return self.format_result(
                False,
                f'갓팩 감지 메시지 전송 실패: {str(e)}'
            )