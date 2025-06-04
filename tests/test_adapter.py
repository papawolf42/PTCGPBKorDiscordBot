#!/usr/bin/env python3
"""
test_adapter.py - LocalFileAdapter 테스트
"""

import LocalFileAdapter as GIST

def test_text_adapter():
    """TEXT 어댑터 테스트"""
    print("=== TEXT 어댑터 테스트 ===")
    
    # Admin 파일 테스트
    admin = GIST.TEXT("dummy_id", "Admin", initial=True, test_mode=False)
    print(f"Admin 데이터 타입: {type(admin.DATA)}")
    print(f"Admin 데이터 수: {len(admin.DATA)}")
    if admin.DATA:
        print(f"Admin 샘플: {list(admin.DATA)[:3]}")
    
    # Group7 온라인 테스트
    group7 = GIST.TEXT("dummy_id", "Group7", initial=True, test_mode=False)
    print(f"\nGroup7 온라인 데이터 수: {len(group7.DATA)}")
    
    return True

def test_json_adapter():
    """JSON 어댑터 테스트"""
    print("\n=== JSON 어댑터 테스트 ===")
    
    # Alliance (멤버) 테스트
    member = GIST.JSON("dummy_id", "Alliance", initial=True, test_mode=False)
    print(f"Member 데이터 타입: {type(member.DATA)}")
    print(f"Member 데이터 수: {len(member.DATA)}")
    if member.DATA:
        keys = list(member.DATA.keys())[:3]
        print(f"Member 키 샘플: {keys}")
    
    # GodPack7 테스트
    godpack7 = GIST.JSON("dummy_id", "GodPack7", initial=True, test_mode=False)
    print(f"\nGodPack7 데이터 수: {len(godpack7.DATA)}")
    
    return True

def test_edit_operations():
    """편집 작업 테스트"""
    print("\n=== 편집 작업 테스트 ===")
    
    # TEXT 편집 테스트
    test_admin = GIST.TEXT("dummy_id", "Admin", initial=True, test_mode=True)
    original_size = len(test_admin.DATA)
    
    # 추가
    test_admin.edit('+', 'test_user_123')
    print(f"추가 후 크기: {original_size} → {len(test_admin.DATA)}")
    
    # 삭제
    test_admin.edit('-', 'test_user_123')
    print(f"삭제 후 크기: {len(test_admin.DATA)}")
    
    # JSON 편집 테스트
    test_member = GIST.JSON("dummy_id", "Alliance", initial=True, test_mode=True)
    
    # 추가
    test_member.edit('+', 'test_key', {'name': 'Test User'})
    print(f"\nJSON 추가: 'test_key' 존재 여부 = {'test_key' in test_member.DATA}")
    
    # 삭제
    test_member.edit('-', 'test_key')
    print(f"JSON 삭제: 'test_key' 존재 여부 = {'test_key' in test_member.DATA}")
    
    return True

def main():
    """메인 테스트 실행"""
    print("LocalFileAdapter 테스트 시작\n")
    
    tests = [
        ("TEXT 어댑터", test_text_adapter),
        ("JSON 어댑터", test_json_adapter),
        ("편집 작업", test_edit_operations)
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
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*50)
    print(f"테스트 결과: {passed}개 통과, {failed}개 실패")
    print("="*50)

if __name__ == "__main__":
    main()