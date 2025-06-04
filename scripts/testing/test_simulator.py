#!/usr/bin/env python3
"""
test_simulator.py - Poke.py 자동화 테스트 시뮬레이터
봇과 테스트 클라이언트를 동시에 실행하여 모든 기능을 자동으로 테스트합니다.

실행 방법:
    python scripts/testing/test_simulator.py
    python scripts/testing/test_simulator.py --stop-on-failure
"""

import discord
import asyncio
import subprocess
import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.modules.paths import get_data_path

# 테스트 케이스 모듈 임포트
from test_cases.base import BaseTestCase
from test_cases.connection import ConnectionTests
from test_cases.messages import MessageTests
from test_cases.commands import CommandTests


class PokeTestSimulator:
    """Poke.py 자동화 테스트 시뮬레이터"""
    
    def __init__(self):
        self.bot_process = None
        self.test_client = None
        self.test_results = []
        self.continue_on_fail = True
        self.start_time = datetime.now()
        self.channels = {}
        self.bot_logs = []
        self.bot_log_task = None
        
        # 테스트 환경 설정
        load_dotenv('.env.test')
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        
        # 테스트 채널 ID
        self.channel_ids = {
            'heartbeat_7': int(os.getenv('TEST_GROUP7_HEARTBEAT_ID', 0)),
            'command_7': int(os.getenv('TEST_GROUP7_COMMAND_ID', 0)),
            'heartbeat_8': int(os.getenv('TEST_GROUP8_HEARTBEAT_ID', 0)),
            'command_8': int(os.getenv('TEST_GROUP8_COMMAND_ID', 0))
        }
        
        # 테스트 데이터 경로
        self.test_data_path = get_data_path('data_test')
        
    async def setup(self):
        """테스트 환경 초기화"""
        print("=== Poke.py 자동화 테스트 시작 ===")
        print(f"시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"테스트 데이터 경로: {self.test_data_path}")
        print()
        
    async def run_single_test(self, test_name, test_func):
        """개별 테스트 실행 및 결과 기록"""
        print(f"\n[테스트] {test_name}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            # 결과 기록
            test_result = {
                'name': test_name,
                'success': result.get('success', False),
                'message': result.get('message', ''),
                'details': result.get('details', {}),
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
            
            self.test_results.append(test_result)
            
            # 결과 출력
            if result['success']:
                print(f"✅ 성공: {result['message']}")
            else:
                print(f"❌ 실패: {result['message']}")
                
            if result.get('details'):
                print(f"   상세: {json.dumps(result['details'], ensure_ascii=False, indent=2)}")
                
            print(f"   소요시간: {duration:.2f}초")
            
            # 실패 시 계속할지 확인
            if not result['success'] and not self.continue_on_fail:
                print("\n테스트 실패로 중단합니다.")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")
            self.test_results.append({
                'name': test_name,
                'success': False,
                'message': f'에러: {str(e)}',
                'duration': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            })
            
            if not self.continue_on_fail:
                return False
            return True
    
    async def monitor_bot_logs(self):
        """봇 프로세스 출력을 백그라운드에서 계속 수집"""
        while self.bot_process and self.bot_process.poll() is None:
            line = self.bot_process.stdout.readline()
            if line:
                line = line.strip()
                self.bot_logs.append(line)
                print(f"[BOT] {line}")
            else:
                await asyncio.sleep(0.1)
    
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        await self.setup()
        
        # 테스트 케이스 인스턴스 생성
        connection = ConnectionTests(self)
        messages = MessageTests(self)
        commands = CommandTests(self)
        base = BaseTestCase(self)
        
        # 테스트 목록 (순차 실행)
        tests = [
            # Phase 1: 초기화
            ("bot_startup", connection.test_bot_startup),
            ("client_connect", connection.test_client_connect),
            ("channel_access", connection.test_channel_access),
            ("data_directory", connection.test_data_directory),
            
            # Phase 2: 메시지 테스트
            ("heartbeat_user1", messages.test_heartbeat_testuser1),
            ("wait_3sec", lambda: base.wait_seconds(3)),
            ("heartbeat_papawolf", messages.test_heartbeat_papawolf),
            ("wait_3sec", lambda: base.wait_seconds(3)),
            ("verify_online", messages.test_verify_online_update),
            
            # Phase 3: 명령어 테스트
            ("cmd_state", commands.test_state_command),
            ("wait_2sec", lambda: base.wait_seconds(2)),
            ("cmd_list", commands.test_list_command),
            ("wait_2sec", lambda: base.wait_seconds(2)),
            ("cmd_barracks", commands.test_barracks_command),
            
            # Phase 4: 테스트 명령어 (관리자)
            ("cmd_test_update", commands.test_test_update_command),
            ("wait_5sec", lambda: base.wait_seconds(5)),
            ("cmd_test_offline", commands.test_test_offline_command),
            
            # Phase 5: 오류 처리
            ("invalid_command", commands.test_invalid_command),
        ]
        
        # 각 테스트 실행
        for test_name, test_func in tests:
            success = await self.run_single_test(test_name, test_func)
            if not success:
                break
            
            # 테스트 간 대기
            await asyncio.sleep(1)
    
    async def cleanup(self):
        """정리 작업"""
        print("\n[정리] 테스트 환경 정리 중...")
        
        # 봇 로그 모니터링 중단
        if self.bot_log_task:
            self.bot_log_task.cancel()
        
        # 테스트 클라이언트 종료
        if self.test_client:
            await self.test_client.close()
        
        # 봇 프로세스 종료
        if self.bot_process:
            self.bot_process.terminate()
            self.bot_process.wait()
            
        print("✅ 정리 완료")
    
    def save_results(self):
        """테스트 결과 저장"""
        results = {
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': str(datetime.now() - self.start_time),
            'total_tests': len(self.test_results),
            'passed_tests': sum(1 for r in self.test_results if r['success']),
            'failed_tests': sum(1 for r in self.test_results if not r['success']),
            'test_results': self.test_results,
            'bot_logs': self.bot_logs[-100:]  # 마지막 100줄만 저장
        }
        
        # 결과 파일 저장
        results_dir = Path(__file__).parent / 'results'
        results_dir.mkdir(exist_ok=True)
        
        filename = results_dir / f"test_results_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 요약 출력
        print("\n=== 테스트 결과 요약 ===")
        print(f"총 테스트: {results['total_tests']}")
        print(f"성공: {results['passed_tests']} ✅")
        print(f"실패: {results['failed_tests']} ❌")
        print(f"소요 시간: {results['duration']}")
        print(f"결과 파일: {filename}")
        
        # 실패한 테스트 목록
        if results['failed_tests'] > 0:
            print("\n실패한 테스트:")
            for test in self.test_results:
                if not test['success']:
                    print(f"  - {test['name']}: {test['message']}")


async def main():
    """메인 실행 함수"""
    # 명령행 인수 파서
    parser = argparse.ArgumentParser(description='Poke.py 자동화 테스트 시뮬레이터')
    parser.add_argument('--stop-on-failure', action='store_true',
                       help='테스트 실패 시 즉시 중단')
    parser.add_argument('--only', type=str,
                       help='특정 테스트만 실행 (예: --only connection)')
    args = parser.parse_args()
    
    # 시뮬레이터 생성
    simulator = PokeTestSimulator()
    
    # 옵션 적용
    if args.stop_on_failure:
        simulator.continue_on_fail = False
    
    try:
        # 모든 테스트 실행
        await simulator.run_all_tests()
        
    except KeyboardInterrupt:
        print("\n\n테스트 중단됨 (Ctrl+C)")
        
    finally:
        # 결과 저장
        simulator.save_results()
        
        # 정리
        await simulator.cleanup()


if __name__ == "__main__":
    # 이벤트 루프 실행
    asyncio.run(main())