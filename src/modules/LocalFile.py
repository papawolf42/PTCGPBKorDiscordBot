"""
LocalFile.py - 로컬 파일 시스템 기반 데이터 저장 모듈
GIST.py와 동일한 인터페이스를 제공하여 GitHub Gist 대신 로컬 파일 사용
"""

import os
import json
import datetime
from typing import Union, List, Dict, Any
import threading

class SERVER:
    """서버 정보 클래스 (GIST.py와 동일)"""
    def __init__(self, timestamp: str = None, godpack_code: List[str] = None, 
                 online_code: List[str] = None, offline_code: List[str] = None):
        self.timestamp = timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.godpack_code = godpack_code or []
        self.online_code = online_code or []
        self.offline_code = offline_code or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "godpack_code": self.godpack_code,
            "online_code": self.online_code,
            "offline_code": self.offline_code
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SERVER':
        return cls(
            timestamp=data.get("timestamp"),
            godpack_code=data.get("godpack_code", []),
            online_code=data.get("online_code", []),
            offline_code=data.get("offline_code", [])
        )

class USER:
    """사용자 정보 클래스 (GIST.py와 동일)"""
    def __init__(self, nick: str, id: str, card: str = None, timestamp: str = None, 
                 state: bool = None, type: str = None):
        self.nick = nick
        self.id = id
        self.card = card or ""
        self.timestamp = timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state = state if state is not None else True
        self.type = type or "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nick": self.nick,
            "id": self.id,
            "card": self.card,
            "timestamp": self.timestamp,
            "state": self.state,
            "type": self.type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'USER':
        return cls(
            nick=data.get("nick", ""),
            id=data.get("id", ""),
            card=data.get("card", ""),
            timestamp=data.get("timestamp"),
            state=data.get("state", True),
            type=data.get("type", "normal")
        )

class LocalFile:
    """로컬 파일 시스템을 사용한 데이터 저장 클래스"""
    
    def __init__(self, base_path: str = None, test_mode: bool = False):
        """
        Args:
            base_path: 데이터 저장 기본 경로
            test_mode: 테스트 모드 여부
        """
        # 환경변수에서 DATA_PATH 가져오기
        DATA_PATH = os.getenv('DATA_PATH', 'data')
        if base_path is None:
            base_path = os.path.join(DATA_PATH, "poke_data")
        self.base_path = base_path if not test_mode else os.path.join(DATA_PATH.replace('data', 'data_test'), "poke_data")
        self._ensure_directories()
        self.lock = threading.Lock()  # 동시 쓰기 방지용 락
    
    def _ensure_directories(self):
        """필요한 디렉토리 구조 생성"""
        groups = ['common', 'group7', 'group8']
        for group in groups:
            group_path = os.path.join(self.base_path, group)
            os.makedirs(group_path, exist_ok=True)
    
    def _get_file_path(self, group: str, filename: str) -> str:
        """파일 경로 생성"""
        # Group7_admin -> group7/admin.txt 형식으로 변환
        group_lower = group.lower()
        if '_' in filename:
            _, file_part = filename.split('_', 1)
            filename = file_part.lower()
        
        # 파일 확장자 결정
        if filename in ['admin', 'online']:
            filename += '.txt'
        elif filename in ['member', 'godpack', 'godpackcode']:
            filename += '.json'
        
        return os.path.join(self.base_path, group_lower, filename)
    
    def uploadFile(self, group: str, filename: str, content: Union[str, List, Dict], 
                   format: str = 'TEXT') -> bool:
        """파일 업로드 (저장)"""
        try:
            with self.lock:
                file_path = self._get_file_path(group, filename)
                
                if format == 'TEXT':
                    # TEXT 형식: 문자열 또는 리스트를 줄바꿈으로 구분
                    if isinstance(content, list):
                        content = '\n'.join(str(item) for item in content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                elif format == 'JSON':
                    # JSON 형식: 딕셔너리 또는 리스트를 JSON으로 저장
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(content, f, ensure_ascii=False, indent=2)
                
                return True
                
        except Exception as e:
            print(f"[LocalFile] 파일 저장 실패: {e}")
            return False
    
    def openFile(self, group: str, filename: str, format: str = 'TEXT') -> Union[str, List, Dict, None]:
        """파일 열기 (읽기)"""
        try:
            file_path = self._get_file_path(group, filename)
            
            if not os.path.exists(file_path):
                # 파일이 없으면 기본값 반환
                if format == 'TEXT':
                    return ""
                elif format == 'JSON':
                    return {} if 'member' in filename or 'godpack' in filename else []
            
            if format == 'TEXT':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # 빈 파일이면 빈 문자열 반환
                    if not content:
                        return ""
                    # 줄바꿈으로 구분된 리스트로 반환
                    return content.split('\n') if '\n' in content else [content] if content else []
            
            elif format == 'JSON':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        except FileNotFoundError:
            # 파일이 없으면 기본값 반환
            if format == 'TEXT':
                return []
            elif format == 'JSON':
                return {} if 'member' in filename or 'godpack' in filename else []
        
        except json.JSONDecodeError:
            print(f"[LocalFile] JSON 파싱 실패: {file_path}")
            return {} if 'member' in filename or 'godpack' in filename else []
        
        except Exception as e:
            print(f"[LocalFile] 파일 읽기 실패: {e}")
            return None
    
    def exists(self, group: str, filename: str) -> bool:
        """파일 존재 여부 확인"""
        file_path = self._get_file_path(group, filename)
        return os.path.exists(file_path)
    
    def backup(self, group: str = None):
        """데이터 백업"""
        try:
            backup_dir = os.path.join(self.base_path, 'backup', 
                                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(backup_dir, exist_ok=True)
            
            if group:
                # 특정 그룹만 백업
                groups = [group]
            else:
                # 전체 백업
                groups = ['group7', 'group8']
            
            for grp in groups:
                src_dir = os.path.join(self.base_path, grp.lower())
                dst_dir = os.path.join(backup_dir, grp.lower())
                if os.path.exists(src_dir):
                    import shutil
                    shutil.copytree(src_dir, dst_dir)
            
            print(f"[LocalFile] 백업 완료: {backup_dir}")
            return True
            
        except Exception as e:
            print(f"[LocalFile] 백업 실패: {e}")
            return False
    
    def parse_godpack(self, message: str) -> tuple:
        """갓팩 메시지 파싱 (GIST.py와 동일한 로직)"""
        lines = message.split('\n')
        player_code = ""
        pack_info = []
        
        for line in lines:
            if "Player" in line and ":" in line:
                player_code = line.split(':')[1].strip()
            elif "Pack" in line and ":" in line:
                pack_num = line.split(':')[0].strip().split()[1]
                pack_code = line.split(':')[1].strip()
                pack_info.append(f"Pack {pack_num}: {pack_code}")
        
        return player_code, pack_info
    
    # GIST.py와의 호환성을 위한 메서드들
    def getGodpackCode(self, group: str) -> List[str]:
        """갓팩 코드 목록 가져오기"""
        data = self.openFile(group, f"{group}_godpackCode", 'JSON')
        return data if isinstance(data, list) else []
    
    def getOnlineUsers(self, group: str) -> List[str]:
        """온라인 사용자 목록 가져오기"""
        data = self.openFile(group, f"{group}_online", 'TEXT')
        return data if isinstance(data, list) else []
    
    def getMembers(self, group: str) -> Dict[str, Dict]:
        """멤버 정보 가져오기"""
        data = self.openFile(group, f"{group}_member", 'JSON')
        return data if isinstance(data, dict) else {}
    
    def getGodpacks(self, group: str) -> Dict[str, Dict]:
        """갓팩 정보 가져오기"""
        data = self.openFile(group, f"{group}_godpack", 'JSON')
        return data if isinstance(data, dict) else {}

# 테스트 코드
if __name__ == "__main__":
    # LocalFile 테스트
    storage = LocalFile(test_mode=True)
    
    # 텍스트 파일 테스트
    print("=== 텍스트 파일 테스트 ===")
    storage.uploadFile("Group7", "Group7_admin", ["admin1", "admin2"], 'TEXT')
    admins = storage.openFile("Group7", "Group7_admin", 'TEXT')
    print(f"관리자 목록: {admins}")
    
    # JSON 파일 테스트
    print("\n=== JSON 파일 테스트 ===")
    test_user = USER("TestUser", "123456789", "TEST-CODE-123")
    members = {"123456789": test_user.to_dict()}
    storage.uploadFile("Group7", "Group7_member", members, 'JSON')
    loaded_members = storage.openFile("Group7", "Group7_member", 'JSON')
    print(f"멤버 정보: {loaded_members}")
    
    # 백업 테스트
    print("\n=== 백업 테스트 ===")
    storage.backup("Group7")