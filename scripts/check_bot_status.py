#!/usr/bin/env python3
"""
check_bot_status.py - 봇 상태 및 데이터 확인
"""

import os
from LocalFile import LocalFile

def check_data_files():
    """로컬 데이터 파일 상태 확인"""
    print("=== 로컬 데이터 파일 상태 ===\n")
    
    storage = LocalFile(test_mode=False)
    
    # 확인할 파일들
    files_to_check = [
        ("Common", "Common_admin", "TEXT"),
        ("Common", "Common_member", "JSON"),
        ("Group7", "Group7_online", "TEXT"),
        ("Group7", "Group7_godpack", "JSON"),
        ("Group7", "Group7_godpackCode", "JSON"),
        ("Group8", "Group8_online", "TEXT"),
        ("Group8", "Group8_godpack", "JSON"),
        ("Group8", "Group8_godpackCode", "JSON")
    ]
    
    for group, filename, format_type in files_to_check:
        if storage.exists(group, filename):
            data = storage.openFile(group, filename, format_type)
            
            if format_type == "TEXT":
                if isinstance(data, list):
                    print(f"✅ {filename}: {len(data)} 항목")
                    if data and len(data) > 0:
                        print(f"   샘플: {data[:2]}")
                else:
                    print(f"✅ {filename}: 빈 파일")
            else:  # JSON
                if isinstance(data, dict):
                    print(f"✅ {filename}: {len(data)} 항목")
                    if data:
                        keys = list(data.keys())[:2]
                        print(f"   키 샘플: {keys}")
                elif isinstance(data, list):
                    print(f"✅ {filename}: {len(data)} 항목")
                    if data:
                        print(f"   샘플: {data[:2]}")
        else:
            print(f"❌ {filename}: 파일 없음")
        print()

def check_test_mode():
    """테스트 모드 환경 확인"""
    print("\n=== 테스트 환경 확인 ===")
    
    # .env.test 파일 확인
    if os.path.exists('.env.test'):
        print("✅ .env.test 파일 존재")
        
        # 주요 환경변수 확인
        from dotenv import dotenv_values
        config = dotenv_values('.env.test')
        
        important_vars = [
            'TEST_MODE',
            'DISCORD_BOT_TOKEN',
            'TEST_MAIN_ID',
            'TEST_GROUP7_HEARTBEAT_ID',
            'TEST_GROUP7_COMMAND_ID',
            'TEST_GROUP8_HEARTBEAT_ID',
            'TEST_GROUP8_COMMAND_ID'
        ]
        
        print("\n환경변수 설정 상태:")
        for var in important_vars:
            if var in config and config[var]:
                print(f"  ✅ {var}: 설정됨")
            else:
                print(f"  ❌ {var}: 미설정")
    else:
        print("❌ .env.test 파일 없음")

if __name__ == "__main__":
    check_data_files()
    check_test_mode()
    
    print("\n=== 봇 실행 명령어 ===")
    print("1. 테스트 봇 실행:")
    print("   python Poke_test.py")
    print("\n2. 백그라운드 실행 (Linux/Mac):")
    print("   nohup python Poke_test.py > poke_test.log 2>&1 &")
    print("\n3. 로그 확인:")
    print("   tail -f poke_test.log")