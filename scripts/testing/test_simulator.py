#!/usr/bin/env python3
"""
test_simulator.py - Poke.py 자동화 테스트 시뮬레이터
봇은 별도로 실행하고, 테스트 클라이언트만 실행하여 기능을 테스트합니다.

실행 방법:
    1. 봇 실행: python tests/Poke_test.py
    2. 테스트 실행: python scripts/testing/test_simulator.py
    3. 디버그 모드: python scripts/testing/test_simulator.py --debug
"""

import discord
import asyncio
import aiohttp
import os
import sys
import json
import time
import argparse
import logging
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.modules.paths import get_data_path, LOGS_DIR, TEST_DATA_DIR

# 테스트 케이스 모듈 임포트
from test_cases.base import BaseTestCase
from test_cases.connection import ConnectionTests
from test_cases.messages import MessageTests
from test_cases.commands import CommandTests
from test_cases.detect_test_data import DETECT_MESSAGE_TEST_CASES, DETECT_QUICK_TEST_CASES, validate_detect_image_files


def setup_logging(debug=False):
    """로깅 설정"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Discord.py의 verbose 로깅 억제
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)  # DEBUG 대신 WARNING 레벨로 설정
    
    # discord.gateway의 heartbeat 경고도 억제 (디버깅 시에만)
    if debug:
        gateway_logger = logging.getLogger('discord.gateway')
        gateway_logger.setLevel(logging.ERROR)  # heartbeat blocked 경고 숨김
    
    # 로그 디렉토리 생성 (프로젝트 루트의 logs 디렉토리 사용)
    log_dir = Path(LOGS_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # 로그 파일명
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"test_{timestamp}.log"
    
    # 로거 설정
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('TestSimulator')
    logger.info(f"로그 파일: {log_file}")
    return logger


class PokeTestSimulator:
    """Poke.py 자동화 테스트 시뮬레이터"""
    
    def __init__(self, debug=False):
        self.test_client = None
        self.test_results = []
        self.continue_on_fail = True
        self.start_time = datetime.now()
        self.channels = {}
        self.debug = debug
        self.logger = setup_logging(debug)
        
        # 테스트 환경 설정
        load_dotenv()  # .env 파일 로드
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        
        # 테스트 채널 ID (봇 응답 확인용)
        # TEST_MODE에서는 TEST 채널 하나만 사용
        self.channel_ids = {
            'heartbeat': int(os.getenv('DISCORD_TEST_HEARTBEAT_ID', 0)),
            'command': int(os.getenv('DISCORD_TEST_COMMAND_ID', 0)),
            'detect': int(os.getenv('DISCORD_TEST_DETECT_ID', 0)),
            'posting': int(os.getenv('DISCORD_TEST_POSTING_ID', 0))
        }
        
        # Webhook URL 설정 (메시지 전송용)
        self.webhook_urls = {
            'heartbeat': os.getenv('DISCORD_TEST_HEARTBEAT_WEBHOOK'),
            'detect': os.getenv('DISCORD_TEST_DETECT_WEBHOOK'),
        }
        
        # aiohttp 세션
        self.session = None
        
        # 테스트 데이터 경로
        self.test_data_path = TEST_DATA_DIR
        
        # 테스트 케이스 데이터
        self.test_cases = DETECT_QUICK_TEST_CASES  # 빠른 테스트용
        
    async def setup_client(self):
        """Discord 클라이언트 설정"""
        self.logger.info("Discord 클라이언트 설정 중...")
        
        # 인텐트 설정
        intents = discord.Intents.default()
        intents.message_content = True
        
        # 클라이언트 생성
        self.test_client = discord.Client(intents=intents)
        
        # 봇 메시지 기록용
        self.bot_messages = []
        self.message_history = []
        
        # 이벤트 핸들러
        @self.test_client.event
        async def on_ready():
            self.logger.info(f"테스트 클라이언트 준비됨: {self.test_client.user}")
            
            # 채널 연결
            for key, channel_id in self.channel_ids.items():
                channel = self.test_client.get_channel(channel_id)
                if channel:
                    self.channels[key] = channel
                    self.logger.debug(f"채널 연결: {key} = #{channel.name}")
                else:
                    self.logger.warning(f"채널 없음: {key} (ID: {channel_id})")
        
        @self.test_client.event
        async def on_message(message):
            """모든 메시지를 캡처하여 로깅"""
            # 자신의 메시지는 무시
            if message.author == self.test_client.user:
                return
            
            # 봇 메시지 기록
            if message.author.bot:
                msg_info = {
                    'timestamp': datetime.now().isoformat(),
                    'author': str(message.author),
                    'channel': str(message.channel),
                    'content': message.content[:200],  # 처음 200자만
                    'full_content': message.content
                }
                self.bot_messages.append(msg_info)
                
                # 실시간 로깅 (디버그 모드에서만)
                if self.debug:
                    self.logger.debug(f"[봇 메시지] {message.author}: {message.content[:100]}...")
            
            # 모든 메시지 히스토리에 추가
            self.message_history.append({
                'timestamp': datetime.now().isoformat(),
                'author': str(message.author),
                'channel': str(message.channel),
                'content': message.content[:100] + ('...' if len(message.content) > 100 else '')
            })
                    
    async def connect(self):
        """Discord 연결"""
        self.logger.info("Discord 연결 시작...")
        await self.test_client.login(self.token)
        
        # 연결 태스크 생성
        connect_task = asyncio.create_task(self.test_client.connect())
        
        # on_ready 이벤트 대기 (최대 10초)
        ready = False
        for _ in range(10):
            if self.test_client.is_ready():
                ready = True
                break
            await asyncio.sleep(1)
            
        if not ready:
            self.logger.error("클라이언트가 준비되지 않았습니다")
            return False
            
        # aiohttp 세션 생성
        self.session = aiohttp.ClientSession()
        
        return True
    
    async def send_webhook_message(self, webhook_url, content, username=None, attachments=None):
        """Webhook을 사용하여 메시지 전송 (이미지 포함 가능)"""
        if not webhook_url:
            self.logger.error("Webhook URL이 설정되지 않았습니다")
            return None
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # 파일 첨부가 있는 경우 multipart/form-data로 전송
        if attachments:
            data = aiohttp.FormData()
            
            # 메시지 데이터
            payload = {
                'content': content,
                'username': username or 'Test User'
            }
            data.add_field('payload_json', json.dumps(payload))
            
            # 이미지 파일 첨부
            files_attached = 0
            for i, attachment_path in enumerate(attachments):
                if attachment_path.exists():
                    with open(attachment_path, 'rb') as f:
                        file_data = f.read()
                        data.add_field(
                            f'file{i}',
                            file_data,
                            filename=attachment_path.name,
                            content_type='image/png'
                        )
                        files_attached += 1
                        self.logger.debug(f"이미지 첨부: {attachment_path.name}")
                else:
                    self.logger.warning(f"이미지 파일 없음: {attachment_path}")
            
            try:
                async with self.session.post(webhook_url, data=data) as response:
                    if response.status in [200, 204]:
                        self.logger.debug(f"Webhook 메시지 전송 성공 (이미지 {files_attached}개 포함): {username}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Webhook 전송 실패: {response.status} - {error_text}")
                        return False
            except Exception as e:
                self.logger.error(f"Webhook 전송 중 오류: {str(e)}")
                return False
        
        # 파일 첨부가 없는 경우 기존 방식
        else:
            payload = {
                'content': content,
                'username': username or 'Test User'
            }
            
            try:
                async with self.session.post(webhook_url, json=payload) as response:
                    if response.status in [200, 204]:
                        self.logger.debug(f"Webhook 메시지 전송 성공: {username}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Webhook 전송 실패: {response.status} - {error_text}")
                        return False
            except Exception as e:
                self.logger.error(f"Webhook 전송 중 오류: {str(e)}")
                return False
        
    async def wait_for_bot(self, timeout=30):
        """봇이 온라인인지 확인"""
        self.logger.info("봇 상태 확인 중...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 각 채널에서 봇 찾기
            for name, channel in self.channels.items():
                if channel:
                    bot_members = [m for m in channel.members if m.bot]
                    if bot_members:
                        self.logger.info(f"✅ 봇 발견: {', '.join(str(b) for b in bot_members)}")
                        return True
                        
            await asyncio.sleep(1)
            
        self.logger.error("❌ 봇을 찾을 수 없습니다")
        return False
        
    async def run_single_test(self, test_name, test_func):
        """개별 테스트 실행"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"테스트: {test_name}")
        
        # 테스트 설명과 기대 동작 로깅
        if hasattr(test_func, '__self__') and hasattr(test_func.__self__, 'description'):
            self.logger.info(f"설명: {test_func.__self__.description}")
            self.logger.info(f"기대 동작: {test_func.__self__.expected_behavior}")
        
        self.logger.info(f"{'='*60}")
        
        # 테스트 시작 전 봇 메시지 개수 기록
        bot_msg_count_before = len(self.bot_messages)
        
        start_time = time.time()
        try:
            # 테스트 실행
            self.logger.debug(f"테스트 '{test_name}' 시작")
            result = await test_func()
            duration = time.time() - start_time
            self.logger.debug(f"테스트 '{test_name}' 완료 - {duration:.2f}초")
            
            # 테스트 중 수신한 봇 메시지 확인
            new_bot_messages = self.bot_messages[bot_msg_count_before:]
            if new_bot_messages:
                self.logger.info(f"봇 응답: {len(new_bot_messages)}개의 메시지 수신")
                for msg in new_bot_messages[:3]:  # 최대 3개까지만 표시
                    self.logger.info(f"  [{msg['author']}] {msg['content']}")
                if len(new_bot_messages) > 3:
                    self.logger.info(f"  ... 외 {len(new_bot_messages) - 3}개 메시지")
            
            # 결과 기록
            test_result = {
                'name': test_name,
                'success': result.get('success', False),
                'message': result.get('message', ''),
                'description': result.get('description', ''),
                'expected': result.get('expected', ''),
                'details': result.get('details', {}),
                'bot_messages': [msg['content'] for msg in new_bot_messages],
                'bot_message_count': len(new_bot_messages),
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
            
            self.test_results.append(test_result)
            
            # 결과 로깅
            if result['success']:
                self.logger.info(f"✅ 성공: {result['message']}")
            else:
                self.logger.error(f"❌ 실패: {result['message']}")
                
            # 상세 정보는 디버그 레벨에 관계없이 항상 표시
            if result.get('details'):
                self.logger.info("테스트 상세 정보:")
                for key, value in result['details'].items():
                    self.logger.info(f"  - {key}: {value}")
                
            self.logger.info(f"소요시간: {duration:.2f}초")
            
            # 실패 시 중단 여부
            if not result['success'] and not self.continue_on_fail:
                self.logger.warning("실패로 인한 테스트 중단")
                return False
                
            return True
            
        except Exception as e:
            self.logger.exception(f"테스트 예외 발생: {test_name}")
            
            self.test_results.append({
                'name': test_name,
                'success': False,
                'message': f'예외: {str(e)}',
                'duration': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            })
            
            if not self.continue_on_fail:
                return False
            return True
    
    async def validate_test_images(self):
        """테스트 이미지 파일 검증"""
        self.logger.info("테스트 이미지 파일 검증 중...")
        
        if validate_detect_image_files():
            return {
                'success': True,
                'message': '모든 테스트 이미지 파일 확인 완료'
            }
        else:
            return {
                'success': False,
                'message': '일부 테스트 이미지 파일이 누락됨'
            }
            
    async def run_all_tests(self):
        """모든 테스트 실행"""
        self.logger.info("="*60)
        self.logger.info("Poke.py 자동화 테스트 시작")
        self.logger.info(f"시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"테스트 데이터: {self.test_data_path}")
        self.logger.info(f"디버그 모드: {self.debug}")
        self.logger.info("="*60)
        
        # 클라이언트 설정
        await self.setup_client()
        
        # Discord 연결
        if not await self.connect():
            self.logger.error("Discord 연결 실패")
            return
            
        # 봇 대기
        if not await self.wait_for_bot():
            self.logger.error("봇이 실행되지 않았습니다. 먼저 봇을 실행해주세요.")
            self.logger.info("실행 명령: python tests/Poke_test.py")
            self.logger.info("또는 Poke.py를 테스트 모드로 실행: TEST_MODE=true python src/bots/Poke.py")
            return
            
        # 테스트 케이스 생성
        connection = ConnectionTests(self)
        messages = MessageTests(self)
        commands = CommandTests(self)
        base = BaseTestCase(self)
        
        # Barrack 테스트 추가
        from test_cases.messages_for_barrack import BarrackMessageTests
        barrack = BarrackMessageTests(self)
        
        # 테스트 목록
        tests = [
            # Phase 1: 연결 확인 (봇 시작 제외) - ✅ 완료
            # ("client_connect", connection.test_client_connect),
            # ("channel_access", connection.test_channel_access),
            # ("data_directory", connection.test_data_directory),
            
            # Phase 2: Barrack 버그 재현 테스트
            ("setup_multiple_users", barrack.test_setup_multiple_users),
            ("wait_5sec", lambda: base.wait_seconds(5)),
            ("barrack_command", barrack.test_barrack_command),
            ("wait_3sec", lambda: base.wait_seconds(3)),
            ("verify_all_users", barrack.test_verify_all_users_shown),
            
            # Phase 3: 갓팩 감지 및 포스팅 플로우 (주석 처리)
            # ("validate_images", lambda: self.validate_test_images()),
            # ("detect_valid_godpack", messages.test_detect_predefined_case('godpack')),
            # ("wait_3sec", lambda: base.wait_seconds(3)),
            # ("detect_invalid_godpack", messages.test_detect_predefined_case('invalid')),
            # ("wait_3sec", lambda: base.wait_seconds(3)),
            # ("detect_double_twostar", messages.test_detect_predefined_case('double_twostar')),
            # ("wait_3sec", lambda: base.wait_seconds(3)),
            
            # Special Card 테스트 (실제 데이터 기반) - 주석 처리
            # ("detect_real_trainer", messages.test_detect_predefined_case('real_trainer')),
            # ("wait_3sec", lambda: base.wait_seconds(3)),
            # ("detect_real_fullart", messages.test_detect_predefined_case('real_fullart')),
            # ("wait_3sec", lambda: base.wait_seconds(3)),
            # ("detect_real_rainbow", messages.test_detect_predefined_case('real_rainbow')),
            # ("wait_3sec", lambda: base.wait_seconds(3)),
            
            # Phase 4: 커뮤니티 투표 검증 플로우
            # TODO: 포럼 포스트 반응 테스트 구현 예정
            # ("vote_good", messages.test_vote_good),
            # ("vote_bad", messages.test_vote_bad),
        ]
        
        # 테스트 실행
        for test_name, test_func in tests:
            if not await self.run_single_test(test_name, test_func):
                break
                
            # 테스트 간 대기
            await asyncio.sleep(1)
            
    async def cleanup(self):
        """정리 작업"""
        self.logger.info("테스트 환경 정리 중...")
        
        if self.test_client:
            await self.test_client.close()
            self.logger.info("클라이언트 종료됨")
            
        if self.session:
            await self.session.close()
            self.logger.info("HTTP 세션 종료됨")
            
    def save_results(self):
        """결과 저장"""
        results = {
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': str(datetime.now() - self.start_time),
            'total_tests': len(self.test_results),
            'passed_tests': sum(1 for r in self.test_results if r['success']),
            'failed_tests': sum(1 for r in self.test_results if not r['success']),
            'debug_mode': self.debug,
            'test_results': self.test_results
        }
        
        # 결과 파일 저장
        results_dir = Path(__file__).parent / 'results'
        results_dir.mkdir(exist_ok=True)
        
        filename = results_dir / f"test_results_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        # 요약 출력
        self.logger.info("\n" + "="*60)
        self.logger.info("테스트 결과 요약")
        self.logger.info("="*60)
        self.logger.info(f"총 테스트: {results['total_tests']}")
        self.logger.info(f"성공: {results['passed_tests']} ✅")
        self.logger.info(f"실패: {results['failed_tests']} ❌")
        self.logger.info(f"소요 시간: {results['duration']}")
        self.logger.info(f"결과 파일: {filename}")
        
        # 봇 메시지 요약
        self.logger.info("\n" + "="*60)
        self.logger.info("봇 응답 요약")
        self.logger.info("="*60)
        self.logger.info(f"총 봇 메시지 수: {len(self.bot_messages)}")
        
        # 채널별 봇 메시지 분류
        channel_messages = {}
        for msg in self.bot_messages:
            channel = msg['channel']
            if channel not in channel_messages:
                channel_messages[channel] = []
            channel_messages[channel].append(msg)
        
        for channel, messages in channel_messages.items():
            self.logger.info(f"\n{channel} 채널: {len(messages)}개 메시지")
            for msg in messages[:3]:  # 채널당 최대 3개까지만 표시
                self.logger.info(f"  - {msg['content'][:100]}...")
        
        # 봇 메시지도 결과에 포함
        results['bot_messages'] = self.bot_messages
        results['bot_message_count'] = len(self.bot_messages)
        
        # 실패 목록
        if results['failed_tests'] > 0:
            self.logger.warning("\n실패한 테스트:")
            for test in self.test_results:
                if not test['success']:
                    self.logger.warning(f"  - {test['name']}: {test['message']}")
                    

async def main():
    """메인 함수"""
    # 명령행 파서
    parser = argparse.ArgumentParser(description='Poke.py 자동화 테스트')
    parser.add_argument('--stop-on-failure', action='store_true',
                       help='첫 실패 시 중단')
    parser.add_argument('--debug', action='store_true',
                       help='디버그 로깅 활성화')
    parser.add_argument('--only', type=str,
                       help='특정 테스트만 실행')
    args = parser.parse_args()
    
    # 시뮬레이터 생성
    simulator = PokeTestSimulator(debug=args.debug)
    
    if args.stop_on_failure:
        simulator.continue_on_fail = False
        
    try:
        # 테스트 실행
        await simulator.run_all_tests()
        
    except KeyboardInterrupt:
        simulator.logger.warning("\n테스트 중단됨 (Ctrl+C)")
        
    finally:
        # 결과 저장
        simulator.save_results()
        
        # 정리
        await simulator.cleanup()
        

if __name__ == "__main__":
    asyncio.run(main())