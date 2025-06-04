"""
messages.py - 메시지 처리 관련 테스트 케이스
Heartbeat 메시지, 온라인 상태 업데이트, 갓팩 감지 등의 테스트
"""

import asyncio
from .base import BaseTestCase


class MessageTests(BaseTestCase):
    """메시지 처리 관련 테스트 케이스"""
    
    async def test_heartbeat_testuser1(self):
        """testuser1 heartbeat 메시지 전송"""
        channel = self.channels.get('heartbeat_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Heartbeat 채널을 찾을 수 없음'
            )
        
        # Heartbeat 메시지 형식
        message_content = '''[온라인 & 대기중]
나의 팩 선호도: 2P
배럭: 피카츄ex★ [178]
유저: testuser1
코드: 1111-2222-3333'''
        
        try:
            message = await channel.send(message_content)
            return self.format_result(
                True,
                'testuser1 heartbeat 메시지 전송 완료',
                {
                    'message_id': str(message.id),
                    'channel': channel.name
                }
            )
        except Exception as e:
            return self.format_result(
                False,
                f'메시지 전송 실패: {str(e)}'
            )
    
    async def test_heartbeat_papawolf(self):
        """papawolf heartbeat 메시지 전송"""
        channel = self.channels.get('heartbeat_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Heartbeat 채널을 찾을 수 없음'
            )
        
        message_content = '''[온라인 & 대기중]
나의 팩 선호도: 3P
배럭: 리자몽ex★ [256]
유저: papawolf
코드: 7080-6165-9378'''
        
        try:
            message = await channel.send(message_content)
            return self.format_result(
                True,
                'papawolf heartbeat 메시지 전송 완료',
                {
                    'message_id': str(message.id),
                    'channel': channel.name
                }
            )
        except Exception as e:
            return self.format_result(
                False,
                f'메시지 전송 실패: {str(e)}'
            )
    
    async def test_verify_online_update(self):
        """온라인 상태 업데이트 확인"""
        # 봇 로그 확인
        log_found = self.check_recent_bot_logs("온라인 유저 수", limit=20)
        
        # 파일 시스템 확인
        online_file_exists = self.check_file_exists('poke_data/group7/online.txt')
        
        # 사용자 확인
        testuser1_online = self.check_user_in_online_list('group7', 'testuser1')
        papawolf_online = self.check_user_in_online_list('group7', 'papawolf')
        
        # member.json 확인
        member_data = self.read_json_file('poke_data/common/member.json')
        has_member_data = member_data is not None
        
        # 성공 조건: 로그가 있거나 파일이 업데이트됨
        success = log_found or (online_file_exists and (testuser1_online or papawolf_online))
        
        return self.format_result(
            success,
            '온라인 상태 업데이트 확인' if success else '온라인 상태 업데이트 실패',
            {
                'log_found': log_found,
                'online_file_exists': online_file_exists,
                'testuser1_online': testuser1_online,
                'papawolf_online': papawolf_online,
                'has_member_data': has_member_data
            }
        )
    
    async def test_godpack_detect_simulation(self):
        """갓팩 감지 시뮬레이션 (옵션)"""
        channel = self.channels.get('detect_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Detect 채널을 찾을 수 없음'
            )
        
        # 갓팩 감지 메시지 형식
        detect_message = '''2025.06.05 12:00 testuser1 1111-2222-3333
뮤츠 ex ★'''
        
        try:
            message = await channel.send(detect_message)
            
            # 봇 반응 대기 (3초)
            await asyncio.sleep(3)
            
            # 로그 확인
            godpack_detected = self.check_recent_bot_logs("갓팩", limit=10)
            
            return self.format_result(
                True,
                '갓팩 감지 메시지 전송 완료',
                {
                    'message_id': str(message.id),
                    'bot_detected': godpack_detected
                }
            )
        except Exception as e:
            return self.format_result(
                False,
                f'갓팩 감지 메시지 전송 실패: {str(e)}'
            )
    
    async def test_group8_heartbeat(self):
        """Group8 heartbeat 메시지 테스트 (옵션)"""
        channel = self.channels.get('heartbeat_8')
        if not channel:
            # Group8이 없을 수도 있으므로 성공으로 처리
            return self.format_result(
                True,
                'Group8 채널이 설정되지 않음 (정상)'
            )
        
        message_content = '''[온라인 & 대기중]
나의 팩 선호도: 2P
배럭: 이브이ex★ [180]
유저: testuser2
코드: 4444-5555-6666'''
        
        try:
            message = await channel.send(message_content)
            
            # 3초 대기
            await asyncio.sleep(3)
            
            # Group8 파일 확인
            group8_online = self.check_file_exists('poke_data/group8/online.txt')
            
            return self.format_result(
                True,
                'Group8 heartbeat 메시지 전송 완료',
                {
                    'message_id': str(message.id),
                    'online_file_exists': group8_online
                }
            )
        except Exception as e:
            return self.format_result(
                False,
                f'Group8 메시지 전송 실패: {str(e)}'
            )