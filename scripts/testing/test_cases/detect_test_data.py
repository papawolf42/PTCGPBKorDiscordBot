"""
detect_test_data.py - DETECT 채널 테스트용 사전 정의 데이터
실제 DATA_DETECT 폴더의 메시지와 이미지를 기반으로 한 테스트 케이스
"""

from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# DATA_DETECT 이미지 경로
IMAGE_DIR = PROJECT_ROOT / "DATA_DETECT" / "media"

# 테스트 케이스 정의
DETECT_MESSAGE_TEST_CASES = {
    "valid_godpack_1": {
        "type": "godpack",
        "message": {
            "content": """@yunpac Shazam!
yunpac426 (9053874066196496)
[2/5][1P][Arceus] God Pack found in instance: 3
File name: 20250420005536_3_Valid_1_packs.xml
Backing up to the Accounts\\GodPacks folder and continuing...""",
            "username": "yunpac426"
        },
        "attachments": [
            IMAGE_DIR / "20250420005536_3_Valid_1_packs-35E3F.png",
            IMAGE_DIR / "20250420005559_3_FRIENDCODE_1_packs-9C36D.png"
        ],
        "expected": {
            "should_create_post": True,
            "status": "YET",
            "user": "yunpac",
            "instance_id": "yunpac426",
            "friend_code": "9053874066196496"
        }
    },
    
    "valid_godpack_2": {
        "type": "godpack",
        "message": {
            "content": """@Saisai Keep up the great work!
Saisai2 (0266352633065275)
[2/5][4P][Arceus] God Pack found in instance: 2
File name: 20250420013345_2_Valid_4_packs.xml
Backing up to the Accounts\\GodPacks folder and continuing...""",
            "username": "Saisai2"
        },
        "attachments": [
            IMAGE_DIR / "20250420013345_2_Valid_4_packs-227F7.png",
            IMAGE_DIR / "20250420013408_2_FRIENDCODE_4_packs-9EDAD.png"
        ],
        "expected": {
            "should_create_post": True,
            "status": "YET",
            "user": "Saisai",
            "instance_id": "Saisai2",
            "friend_code": "0266352633065275"
        }
    },
    
    "invalid_godpack_1": {
        "type": "invalid",
        "message": {
            "content": """@otter Whoops!
otter154 (9152638166623166)
[1/5][2P][Shining] Invalid God Pack found in instance: 1
File name: 20250420002234_1_Invalid_2_packs.xml
Backing up to the Accounts\\GodPacks folder and continuing...""",
            "username": "otter154"
        },
        "attachments": [
            IMAGE_DIR / "20250420002234_1_Invalid_2_packs-2AB55.png",
            IMAGE_DIR / "20250420002302_1_FRIENDCODE_2_packs-659CE.png"
        ],
        "expected": {
            "should_create_post": False,
            "status": None,
            "user": "otter",
            "instance_id": "otter154",
            "friend_code": "9152638166623166"
        }
    },
    
    "invalid_godpack_2": {
        "type": "invalid",
        "message": {
            "content": """@laff That didn't go as planned.
laff155 (6855906683167259)
[1/5][2P][Shining] Invalid God Pack found in instance: 3
File name: 20250420030613_3_Invalid_1_packs.xml
Backing up to the Accounts\\GodPacks folder and continuing...""",
            "username": "laff155"
        },
        "attachments": [
            IMAGE_DIR / "20250420030613_3_Invalid_1_packs-9B6D5.png",
            IMAGE_DIR / "20250420030637_3_FRIENDCODE_1_packs-95067.png"
        ],
        "expected": {
            "should_create_post": False,
            "status": None,
            "user": "laff",
            "instance_id": "laff155",
            "friend_code": "6855906683167259"
        }
    },
    
    "double_twostar_1": {
        "type": "double_twostar",
        "message": {
            "content": """@Rami Double two star found by Rami108 (9916373212586374) in instance: 3 (1 packs, Dialga)""",
            "username": "Rami108"
        },
        "attachments": [
            IMAGE_DIR / "20250420014118_3_Double_two_star_1_packs-CA653.png",
            IMAGE_DIR / "20250420014142_3_FRIENDCODE_1_packs-55225.png"
        ],
        "expected": {
            "should_create_post": True,  # Double two star도 포스팅함
            "status": None,
            "user": "Rami",
            "instance_id": "Rami108",
            "friend_code": "9916373212586374"
        }
    },
    
    "double_twostar_2": {
        "type": "double_twostar",
        "message": {
            "content": """@Saisai Double two star found by Saisai10 (9925206608231373) in instance: 1 (3 packs, Shining)""",
            "username": "Saisai10"
        },
        "attachments": [
            IMAGE_DIR / "20250420025944_1_Double_two_star_3_packs-C969F.png",
            IMAGE_DIR / "20250420030006_1_FRIENDCODE_3_packs-BB010.png"
        ],
        "expected": {
            "should_create_post": True,  # Double two star도 포스팅함
            "status": None,
            "user": "Saisai",
            "instance_id": "Saisai10",
            "friend_code": "9925206608231373"
        }
    },
    
    # === 실제 데이터 기반 Special Card Found 테스트 케이스들 ===
    
    "real_trainer_case_1": {
        "type": "special",
        "message": {
            "content": """@MinMin Trainer found by 「NEQI ㆍ귀이이 1.•넅 (5536319345500719) in instance: 1 (1 packs, Palkia)
File name: 20250606130619_1_Trainer_1_packs.xml
Backing up to the Accounts\\SpecificCards folder and continuing...""",
            "username": "「NEQI ㆍ귀이이 1.•넅"
        },
        "attachments": [
            IMAGE_DIR.parent / "media2" / "20250606130619_1_Trainer_1_packs-7B74E.png",
            IMAGE_DIR.parent / "media2" / "20250606130641_1_FRIENDCODE_1_packs-08C91.png"
        ],
        "expected": {
            "should_create_post": True,
            "status": "YET",
            "user": "MinMin",
            "instance_id": "「NEQI ㆍ귀이이 1.•넅",
            "friend_code": "5536319345500719",
            "card_type": "Trainer",
            "packs": "1",
            "open_pack": "Palkia"
        }
    },
    
    "real_trainer_case_2": {
        "type": "special",
        "message": {
            "content": """@RKLB Trainer found by 들!,근의 ㆍ테이|:l !|년 (5494037701300243) in instance: 1 (2 packs, Buzzwole)
File name: 20250606214431_1_Trainer_2_packs.xml
Backing up to the Accounts\\SpecificCards folder and continuing...""",
            "username": "들!,근의 ㆍ테이|:l !|년"
        },
        "attachments": [
            IMAGE_DIR.parent / "media2" / "20250606214431_1_Trainer_2_packs-161E8.png",
            IMAGE_DIR.parent / "media2" / "20250606214453_1_FRIENDCODE_2_packs-ED9A8.png"
        ],
        "expected": {
            "should_create_post": True,
            "status": "YET",
            "user": "RKLB",
            "instance_id": "들!,근의 ㆍ테이|:l !|년",
            "friend_code": "5494037701300243",
            "card_type": "Trainer",
            "packs": "2",
            "open_pack": "Buzzwole"
        }
    },
    
    "real_fullart_case": {
        "type": "special",
        "message": {
            "content": """@1tori Full Art found by 「NEQI ㆍ귀이이 1.•넅 (3427135381459652) in instance: 4 (2 packs, Solgaleo)
File name: 20250606224700_4_Full Art_2_packs.xml
Backing up to the Accounts\\SpecificCards folder and continuing...""",
            "username": "「NEQI ㆍ귀이이 1.•넅"
        },
        "attachments": [
            IMAGE_DIR.parent / "media2" / "20250606224700_4_Full_Art_2_packs-D56F8.png",
            IMAGE_DIR.parent / "media2" / "20250606224723_4_FRIENDCODE_2_packs-C9EC1.png"
        ],
        "expected": {
            "should_create_post": True,
            "status": "YET",
            "user": "1tori",
            "instance_id": "「NEQI ㆍ귀이이 1.•넅",
            "friend_code": "3427135381459652",
            "card_type": "Full Art",
            "packs": "2",
            "open_pack": "Solgaleo"
        }
    },
    
    "real_rainbow_case": {
        "type": "special",
        "message": {
            "content": """@1tori Rainbow found by 「NEQI ㆍ귀이이 1.•넅 (0381638991048589) in instance: 2 (2 packs, Buzzwole)
File name: 20250606224803_2_Rainbow_2_packs.xml
Backing up to the Accounts\\SpecificCards folder and continuing...""",
            "username": "「NEQI ㆍ귀이이 1.•넅"
        },
        "attachments": [
            IMAGE_DIR.parent / "media2" / "20250606224803_2_Rainbow_2_packs-9E47B.png",
            IMAGE_DIR.parent / "media2" / "20250606224826_2_FRIENDCODE_2_packs-2DCE6.png"
        ],
        "expected": {
            "should_create_post": True,
            "status": "YET",
            "user": "1tori",
            "instance_id": "「NEQI ㆍ귀이이 1.•넅",
            "friend_code": "0381638991048589",
            "card_type": "Rainbow",
            "packs": "2",
            "open_pack": "Buzzwole"
        }
    },
    
    "real_trainer_solgaleo": {
        "type": "special",
        "message": {
            "content": """@RKLB Trainer found by 「NEQI ㆍ귀이이 1.•넅 (9668298884626731) in instance: 4 (1 packs, Solgaleo)
File name: 20250606215459_4_Trainer_1_packs.xml
Backing up to the Accounts\\SpecificCards folder and continuing...""",
            "username": "「NEQI ㆍ귀이이 1.•넅"
        },
        "attachments": [
            IMAGE_DIR.parent / "media2" / "20250606215459_4_Trainer_1_packs-8423B.png",
            IMAGE_DIR.parent / "media2" / "20250606215523_4_FRIENDCODE_1_packs-2BB20.png"
        ],
        "expected": {
            "should_create_post": True,
            "status": "YET",
            "user": "RKLB",
            "instance_id": "「NEQI ㆍ귀이이 1.•넅",
            "friend_code": "9668298884626731",
            "card_type": "Trainer",
            "packs": "1",
            "open_pack": "Solgaleo"
        }
    }
}

# 빠른 테스트용 샘플 (각 타입별 1개씩)
DETECT_QUICK_TEST_CASES = {
    "godpack": DETECT_MESSAGE_TEST_CASES["valid_godpack_1"],
    "invalid": DETECT_MESSAGE_TEST_CASES["invalid_godpack_1"],
    "double_twostar": DETECT_MESSAGE_TEST_CASES["double_twostar_1"],
    "real_trainer": DETECT_MESSAGE_TEST_CASES["real_trainer_case_1"],
    "real_fullart": DETECT_MESSAGE_TEST_CASES["real_fullart_case"],
    "real_rainbow": DETECT_MESSAGE_TEST_CASES["real_rainbow_case"]
}

def get_detect_test_case(case_name):
    """특정 테스트 케이스 반환"""
    return DETECT_MESSAGE_TEST_CASES.get(case_name)

def get_detect_test_cases_by_type(godpack_type):
    """특정 타입의 모든 테스트 케이스 반환"""
    return {k: v for k, v in DETECT_MESSAGE_TEST_CASES.items() if v["type"] == godpack_type}

def validate_detect_image_files():
    """모든 테스트 케이스의 이미지 파일 존재 여부 확인"""
    missing_files = []
    for case_name, case_data in DETECT_MESSAGE_TEST_CASES.items():
        for img_path in case_data["attachments"]:
            if not img_path.exists():
                missing_files.append(f"{case_name}: {img_path.name}")
    
    if missing_files:
        print(f"⚠️  누락된 이미지 파일 {len(missing_files)}개:")
        for f in missing_files[:5]:  # 최대 5개만 표시
            print(f"   - {f}")
        if len(missing_files) > 5:
            print(f"   ... 외 {len(missing_files) - 5}개")
    else:
        print("✅ 모든 이미지 파일 확인 완료")
    
    return len(missing_files) == 0