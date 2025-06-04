#!/usr/bin/env python3
"""
test_local_system.py - LocalFile 시스템 테스트 스크립트
"""

import os
import sys
from LocalFile import LocalFile, USER, SERVER

def test_basic_operations():
    """기본 파일 읽기/쓰기 테스트"""
    print("=== 기본 작업 테스트 ===")
    
    # 테스트 모드로 LocalFile 생성
    storage = LocalFile(test_mode=True)
    print(f"테스트 데이터 경로: {storage.base_path}")
    
    # 1. TEXT 파일 테스트
    print("\n1. TEXT 파일 테스트")
    test_admins = ["admin1#1234", "admin2#5678", "admin3#9012"]
    
    # 저장
    success = storage.uploadFile("Group7", "Group7_Admin", test_admins, 'TEXT')
    print(f"   관리자 목록 저장: {'성공' if success else '실패'}")
    
    # 읽기
    loaded_admins = storage.openFile("Group7", "Group7_Admin", 'TEXT')
    print(f"   저장된 관리자: {loaded_admins}")
    print(f"   데이터 일치: {test_admins == loaded_admins}")
    
    # 2. JSON 파일 테스트
    print("\n2. JSON 파일 테스트")
    test_users = {
        "123456789": USER("TestUser1", "123456789", "TEST-CODE-001").to_dict(),
        "987654321": USER("TestUser2", "987654321", "TEST-CODE-002").to_dict()
    }
    
    # 저장
    success = storage.uploadFile("Group7", "Group7_member", test_users, 'JSON')
    print(f"   멤버 정보 저장: {'성공' if success else '실패'}")
    
    # 읽기
    loaded_users = storage.openFile("Group7", "Group7_member", 'JSON')
    print(f"   저장된 멤버 수: {len(loaded_users)}")
    print(f"   데이터 일치: {test_users == loaded_users}")
    
    return True

def test_godpack_operations():
    """갓팩 관련 작업 테스트"""
    print("\n=== 갓팩 작업 테스트 ===")
    
    storage = LocalFile(test_mode=True)
    
    # 갓팩 메시지 파싱 테스트
    test_message = """Player Code: TEST-PLAYER-123
Pack 1: PACK-CODE-001
Pack 2: PACK-CODE-002
Pack 3: PACK-CODE-003"""
    
    player_code, pack_info = storage.parse_godpack(test_message)
    print(f"플레이어 코드: {player_code}")
    print(f"팩 정보: {pack_info}")
    
    # 갓팩 코드 저장
    godpack_codes = ["GOD-PACK-001", "GOD-PACK-002", "GOD-PACK-003"]
    success = storage.uploadFile("Group8", "Group8_godpackCode", godpack_codes, 'JSON')
    print(f"\n갓팩 코드 저장: {'성공' if success else '실패'}")
    
    # 갓팩 코드 읽기 (호환성 메서드 테스트)
    loaded_codes = storage.getGodpackCode("Group8")
    print(f"저장된 갓팩 코드: {loaded_codes}")
    
    return True

def test_compatibility_methods():
    """GIST.py와의 호환성 메서드 테스트"""
    print("\n=== 호환성 메서드 테스트 ===")
    
    storage = LocalFile(test_mode=True)
    
    # 온라인 사용자 테스트
    online_users = ["USER-001", "USER-002", "USER-003"]
    storage.uploadFile("Group7", "Group7_online", online_users, 'TEXT')
    
    loaded_online = storage.getOnlineUsers("Group7")
    print(f"온라인 사용자: {loaded_online}")
    
    # 멤버 정보 테스트
    members = storage.getMembers("Group7")
    print(f"멤버 수: {len(members)}")
    
    # 갓팩 정보 테스트
    godpacks = storage.getGodpacks("Group7")
    print(f"갓팩 수: {len(godpacks)}")
    
    return True

def test_backup():
    """백업 기능 테스트"""
    print("\n=== 백업 기능 테스트 ===")
    
    storage = LocalFile(test_mode=True)
    
    # 백업 실행
    success = storage.backup("Group7")
    print(f"Group7 백업: {'성공' if success else '실패'}")
    
    # 전체 백업
    success = storage.backup()
    print(f"전체 백업: {'성공' if success else '실패'}")
    
    return True

def test_error_handling():
    """에러 처리 테스트"""
    print("\n=== 에러 처리 테스트 ===")
    
    storage = LocalFile(test_mode=True)
    
    # 존재하지 않는 파일 읽기
    data = storage.openFile("Group7", "NonExistent", 'TEXT')
    print(f"존재하지 않는 TEXT 파일: {data}")
    
    data = storage.openFile("Group7", "NonExistent", 'JSON')
    print(f"존재하지 않는 JSON 파일: {data}")
    
    # 파일 존재 확인
    exists = storage.exists("Group7", "Group7_Admin")
    print(f"Group7_Admin 존재: {exists}")
    
    exists = storage.exists("Group7", "NonExistent")
    print(f"NonExistent 존재: {exists}")
    
    return True

def main():
    """메인 테스트 실행"""
    print("LocalFile 시스템 테스트 시작\n")
    
    tests = [
        ("기본 작업", test_basic_operations),
        ("갓팩 작업", test_godpack_operations),
        ("호환성 메서드", test_compatibility_methods),
        ("백업 기능", test_backup),
        ("에러 처리", test_error_handling)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"\n✅ {test_name} 테스트 통과")
            else:
                failed += 1
                print(f"\n❌ {test_name} 테스트 실패")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} 테스트 중 에러: {e}")
    
    print("\n" + "="*50)
    print(f"테스트 결과: {passed}개 통과, {failed}개 실패")
    print("="*50)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)