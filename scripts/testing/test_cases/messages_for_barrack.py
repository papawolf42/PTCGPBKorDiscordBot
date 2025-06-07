"""
messages_for_barrack.py - Barrack 명령어 테스트를 위한 메시지 처리
Group8의 barrack 버그 재현을 위한 테스트 케이스
"""

import asyncio
import random
from pathlib import Path
from .base import BaseTestCase


class BarrackMessageTests(BaseTestCase):
    """Barrack 관련 메시지 처리 테스트"""
    
    def __init__(self, simulator):
        super().__init__(simulator)
        # member.json에서 사용자 정보 로드
        self.member_data = self.read_json_file('poke_data/common/member.json') or {}
        
        # 테스트용 사용자 목록 (Group8 테스트를 위해 7명 설정)
        # 실제 member.json의 사용자들 사용
        self.test_users = [
            {'name': 'Crowner', 'code': self.member_data.get('Crowner', '6425571125962870')},
            {'name': 'papawolf', 'code': self.member_data.get('papawolf', '2385424525569486')},
            {'name': 'Paul', 'code': self.member_data.get('Paul', '5131336300012764')},
            {'name': 'PIKACHU', 'code': self.member_data.get('PIKACHU', '7996221063208776')},
            {'name': 'LEE', 'code': self.member_data.get('LEE', '3820667096525835')},
            {'name': 'June', 'code': self.member_data.get('June', '1200153476398146')},
            {'name': 'RYAN', 'code': self.member_data.get('RYAN', '6214223248269382')}
        ]
    
    def create_heartbeat_message(self, username, time_minutes=150, packs=421, online_accounts="Main, 1, 2, 3, 4", offline_accounts="none"):
        """Barrack 테스트용 heartbeat 메시지 생성"""
        if time_minutes == 0:
            avg = 0.00
        else:
            avg = packs / time_minutes
        
        # 다양한 팩 타입과 버전
        pack_types = ["Arceus", "Palkia", "Dialga", "Mew", "Charizard", "Pikachu"]
        opening_packs = random.sample(pack_types, k=2)
        opening = ', '.join(opening_packs) + ','
        
        versions = ["mixman208-v6.4.14", "Arturo-v6.3.29", "Letsw-v6.5.2"]
        version = random.choice(versions)
        
        types = ["Inject for Reroll (1P Method)", "5 Pack (Fast) (Menu Delete)", "Normal Opening"]
        type_str = random.choice(types)
        
        return f'''{username}
Online: {online_accounts}
Offline: {offline_accounts}
Time: {time_minutes}m Packs: {packs} | Avg: {avg:.2f} packs/min
Version: {version}
Type: {type_str}
Opening: {opening}'''
    
    async def test_setup_multiple_users(self):
        """여러 사용자를 온라인으로 설정 (Group8 시뮬레이션)"""
        self.description = "Group8에 7명의 사용자를 온라인으로 설정"
        self.expected_behavior = "모든 사용자가 online.txt에 추가되고 메모리에 유지됨"
        
        # Webhook URL 확인
        webhook_url = self.simulator.webhook_urls.get('heartbeat')
        if not webhook_url:
            return self.format_result(
                False,
                'Heartbeat webhook URL이 설정되지 않음'
            )
        
        success_count = 0
        failed_users = []
        
        self.simulator.logger.info(f"전송할 사용자 수: {len(self.test_users)}명")
        self.simulator.logger.info(f"사용자 목록: {[u['name'] for u in self.test_users]}")
        
        # 각 사용자에 대해 heartbeat 메시지 전송
        for i, user in enumerate(self.test_users):
            try:
                # 각 사용자별로 다른 시간과 팩 수 설정
                time_min = 100 + (i * 20)  # 100분부터 20분씩 증가
                packs = 200 + (i * 50)     # 200팩부터 50팩씩 증가
                
                message_content = self.create_heartbeat_message(
                    user['name'], 
                    time_minutes=time_min,
                    packs=packs
                )
                
                self.simulator.logger.info(f"[{i+1}/{len(self.test_users)}] {user['name']} heartbeat 전송 중...")
                
                # Webhook으로 메시지 전송
                sent = await self.simulator.send_webhook_message(
                    webhook_url, 
                    message_content, 
                    username=user['name']
                )
                
                if sent:
                    success_count += 1
                    self.simulator.logger.info(f"✅ {user['name']} heartbeat 전송 성공")
                else:
                    failed_users.append(user['name'])
                    self.simulator.logger.error(f"❌ {user['name']} heartbeat 전송 실패")
                
                # 메시지 간 짧은 대기
                await asyncio.sleep(1)  # 0.5초에서 1초로 늘림
                
            except Exception as e:
                failed_users.append(user['name'])
                self.simulator.logger.error(f"❌ {user['name']} 처리 중 오류: {str(e)}")
        
        # 봇 처리 대기
        await asyncio.sleep(3)
        
        # online.txt 확인 (TEST_MODE에서는 test 디렉토리 사용)
        online_content = self.read_file_content('poke_data/test/online.txt')
        online_users = []
        if online_content:
            lines = online_content.strip().split('\n')
            for line in lines:
                if line.strip():
                    online_users.append(line.strip())
        
        return self.format_result(
            success_count == len(self.test_users),
            f'{success_count}/{len(self.test_users)}명의 사용자 온라인 설정 완료',
            {
                'total_users': len(self.test_users),
                'success_count': success_count,
                'failed_users': failed_users,
                'online_txt_count': len(online_users),
                'online_users': online_users
            }
        )
    
    async def test_barrack_command(self):
        """!barrack 명령어 실행 및 응답 확인"""
        self.description = "!barrack 명령어로 온라인 사용자 목록 확인"
        self.expected_behavior = "봇이 모든 온라인 사용자와 배럭 정보를 표시"
        
        # 명령어 채널 확인
        command_channel = self.channels.get('command')
        if not command_channel:
            return self.format_result(
                False,
                'Command 채널을 찾을 수 없음'
            )
        
        self.simulator.logger.info(f"Command 채널: {command_channel.name} (ID: {command_channel.id})")
        
        try:
            # 봇 응답 준비
            bot_msg_count_before = len(self.simulator.bot_messages)
            self.simulator.logger.info(f"현재 봇 메시지 수: {bot_msg_count_before}")
            
            # !barracks 명령어 전송 (복수형)
            await command_channel.send("!barracks")
            self.simulator.logger.info("!barracks 명령어 전송")
            
            # 봇 응답 대기
            await asyncio.sleep(5)
            
            # 봇 응답 확인
            new_bot_messages = self.simulator.bot_messages[bot_msg_count_before:]
            barrack_response = None
            
            for msg in new_bot_messages:
                if '현재 온라인 상태' in msg['content'] or 'barrack' in msg['content'].lower():
                    barrack_response = msg
                    break
            
            if not barrack_response:
                return self.format_result(
                    False,
                    'Barrack 응답을 받지 못함',
                    {
                        'bot_messages_received': len(new_bot_messages),
                        'messages': [msg['content'][:100] for msg in new_bot_messages]
                    }
                )
            
            # 응답 내용 분석
            response_content = barrack_response['full_content']
            
            # 온라인 사용자 수 추출
            import re
            online_match = re.search(r'현재 온라인 상태 \((\d+)명', response_content)
            online_count = int(online_match.group(1)) if online_match else 0
            
            # 각 사용자 정보 추출
            user_lines = []
            lines = response_content.split('\n')
            for line in lines:
                if ':' in line and any(user['name'] in line for user in self.test_users):
                    user_lines.append(line.strip())
            
            # 성공 여부 판단
            success = online_count >= 6  # 최소 6명 이상이어야 성공
            
            return self.format_result(
                success,
                f'Barrack 명령어 응답 확인 - {online_count}명 온라인',
                {
                    'online_count_in_response': online_count,
                    'expected_count': len(self.test_users),
                    'user_lines_found': len(user_lines),
                    'sample_users': user_lines[:3] if user_lines else [],
                    'response_length': len(response_content),
                    'response_preview': response_content[:200] + '...' if len(response_content) > 200 else response_content
                }
            )
            
        except Exception as e:
            return self.format_result(
                False,
                f'Barrack 명령어 실행 중 오류: {str(e)}'
            )
    
    async def test_verify_all_users_shown(self):
        """모든 사용자가 barrack 응답에 표시되는지 확인"""
        self.description = "Barrack 응답에 모든 7명의 사용자가 표시되는지 검증"
        self.expected_behavior = "설정한 7명의 사용자가 모두 응답에 포함됨"
        
        # 가장 최근 barrack 응답 찾기
        barrack_response = None
        for msg in reversed(self.simulator.bot_messages):
            if '현재 온라인 상태' in msg.get('content', ''):
                barrack_response = msg
                break
        
        if not barrack_response:
            return self.format_result(
                False,
                'Barrack 응답을 찾을 수 없음'
            )
        
        response_content = barrack_response['full_content']
        
        # 각 사용자가 응답에 포함되어 있는지 확인
        found_users = []
        missing_users = []
        
        for user in self.test_users:
            if user['name'] in response_content:
                found_users.append(user['name'])
            else:
                missing_users.append(user['name'])
        
        # FILE.DATA와 Server.ONLINE 정보도 확인 (디버깅용)
        online_file_content = self.read_file_content('poke_data/test/online.txt')
        file_users = []
        file_codes = []
        if online_file_content:
            lines = online_file_content.strip().split('\n')
            for line in lines:
                if line.strip():
                    file_codes.append(line.strip())
                    # 친구코드만 저장되어 있으므로 매칭
                    for user in self.test_users:
                        if user['code'] == line.strip():
                            file_users.append(user['name'])
                            break
        
        success = len(missing_users) == 0
        
        return self.format_result(
            success,
            f'{len(found_users)}/{len(self.test_users)}명의 사용자가 barrack에 표시됨',
            {
                'total_users': len(self.test_users),
                'found_users': found_users,
                'missing_users': missing_users,
                'file_users': file_users,
                'file_user_count': len(file_users),
                'file_codes': file_codes[:3] if file_codes else [],  # 처음 3개만 표시
                'bug_reproduced': not success and len(found_users) < len(file_users)
            }
        )