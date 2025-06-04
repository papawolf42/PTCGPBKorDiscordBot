"""
commands.py - 명령어 관련 테스트 케이스
봇 명령어 응답, 관리자 명령어, 테스트 명령어 등의 테스트
"""

import asyncio
from .base import BaseTestCase


class CommandTests(BaseTestCase):
    """명령어 관련 테스트 케이스"""
    
    async def test_state_command(self):
        """!state 명령어 테스트"""
        channel = self.channels.get('command_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Command 채널을 찾을 수 없음'
            )
        
        try:
            # 명령어 전송
            command_msg = await channel.send("!state")
            
            # 봇 응답 대기
            response = await self.wait_for_bot_response(channel, command_msg)
            
            if response:
                # 응답 내용 분석
                has_online_count = "온라인" in response.content
                has_godpack_info = "갓팩" in response.content or "레어팩" in response.content
                
                return self.format_result(
                    True,
                    '!state 명령어 응답 수신',
                    {
                        'response_preview': response.content[:100] + '...' if len(response.content) > 100 else response.content,
                        'has_online_count': has_online_count,
                        'has_godpack_info': has_godpack_info
                    }
                )
            else:
                return self.format_result(
                    False,
                    '!state 명령어 응답 시간 초과'
                )
                
        except Exception as e:
            return self.format_result(
                False,
                f'명령어 전송 실패: {str(e)}'
            )
    
    async def test_list_command(self):
        """!list 명령어 테스트"""
        channel = self.channels.get('command_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Command 채널을 찾을 수 없음'
            )
        
        try:
            command_msg = await channel.send("!list")
            response = await self.wait_for_bot_response(channel, command_msg)
            
            if response:
                # Embed 확인
                has_embed = len(response.embeds) > 0
                
                # 파일 첨부 확인 (online.txt 등)
                has_attachment = len(response.attachments) > 0
                
                details = {
                    'has_embed': has_embed,
                    'embed_count': len(response.embeds),
                    'has_attachment': has_attachment,
                    'attachment_count': len(response.attachments)
                }
                
                # Embed 내용 확인
                if has_embed:
                    embed = response.embeds[0]
                    details['embed_title'] = embed.title
                    details['field_count'] = len(embed.fields)
                
                return self.format_result(
                    True,
                    '!list 명령어 응답 수신',
                    details
                )
            else:
                return self.format_result(
                    False,
                    '!list 명령어 응답 시간 초과'
                )
                
        except Exception as e:
            return self.format_result(
                False,
                f'명령어 전송 실패: {str(e)}'
            )
    
    async def test_barracks_command(self):
        """!barracks 명령어 테스트"""
        channel = self.channels.get('command_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Command 채널을 찾을 수 없음'
            )
        
        try:
            command_msg = await channel.send("!barracks")
            response = await self.wait_for_bot_response(channel, command_msg, timeout=10.0)
            
            if response:
                # 파일 첨부 확인 (배럭 목록)
                has_file = len(response.attachments) > 0
                
                return self.format_result(
                    True,
                    '!barracks 명령어 응답 수신',
                    {
                        'has_file': has_file,
                        'response_length': len(response.content)
                    }
                )
            else:
                return self.format_result(
                    False,
                    '!barracks 명령어 응답 시간 초과'
                )
                
        except Exception as e:
            return self.format_result(
                False,
                f'명령어 전송 실패: {str(e)}'
            )
    
    async def test_test_update_command(self):
        """!test_update 명령어 테스트 (관리자 전용)"""
        channel = self.channels.get('command_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Command 채널을 찾을 수 없음'
            )
        
        try:
            # 초기 온라인 수 확인
            initial_online = self.read_file_content('poke_data/group7/online.txt')
            
            # 명령어 전송
            command_msg = await channel.send("!test_update")
            
            # 봇 작업 대기 (업데이트 처리 시간)
            await asyncio.sleep(5)
            
            # 로그 확인
            update_started = self.check_recent_bot_logs("온라인 상태 업데이트", limit=20)
            
            # 파일 변경 확인
            final_online = self.read_file_content('poke_data/group7/online.txt')
            file_changed = initial_online != final_online
            
            return self.format_result(
                True,
                '!test_update 명령어 전송 완료',
                {
                    'update_started': update_started,
                    'file_changed': file_changed,
                    'initial_size': len(initial_online) if initial_online else 0,
                    'final_size': len(final_online) if final_online else 0
                }
            )
                
        except Exception as e:
            return self.format_result(
                False,
                f'명령어 전송 실패: {str(e)}'
            )
    
    async def test_test_offline_command(self):
        """!test_offline 명령어 테스트 (관리자 전용)"""
        channel = self.channels.get('command_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Command 채널을 찾을 수 없음'
            )
        
        try:
            # 명령어 전송
            command_msg = await channel.send("!test_offline")
            
            # 처리 대기
            await asyncio.sleep(3)
            
            # 로그 확인
            offline_processed = self.check_recent_bot_logs("오프라인", limit=20)
            
            # 응답 확인
            response = await self.wait_for_bot_response(channel, command_msg, timeout=5.0)
            
            return self.format_result(
                True,
                '!test_offline 명령어 전송 완료',
                {
                    'offline_processed': offline_processed,
                    'got_response': response is not None
                }
            )
                
        except Exception as e:
            return self.format_result(
                False,
                f'명령어 전송 실패: {str(e)}'
            )
    
    async def test_invalid_command(self):
        """존재하지 않는 명령어 테스트"""
        channel = self.channels.get('command_7')
        if not channel:
            return self.format_result(
                False,
                'Group7 Command 채널을 찾을 수 없음'
            )
        
        try:
            # 존재하지 않는 명령어
            command_msg = await channel.send("!notexistcommand")
            
            # 봇이 응답하지 않아야 함 (3초 대기)
            response = await self.wait_for_bot_response(channel, command_msg, timeout=3.0)
            
            # 응답이 없어야 정상
            if response is None:
                return self.format_result(
                    True,
                    '존재하지 않는 명령어에 응답하지 않음 (정상)'
                )
            else:
                return self.format_result(
                    False,
                    '존재하지 않는 명령어에 응답함',
                    {'response': response.content[:50]}
                )
                
        except Exception as e:
            return self.format_result(
                False,
                f'명령어 전송 실패: {str(e)}'
            )