"""
LocalFileAdapter.py - GIST 인터페이스를 LocalFile로 변환하는 어댑터
"""

from LocalFile import LocalFile as LocalFileBase

class LocalFileAdapter:
    """GIST 클래스와 동일한 인터페이스를 제공하는 LocalFile 어댑터"""
    
    def __init__(self, group, filename, format_type='JSON', test_mode=False):
        """
        Args:
            group: 그룹명 (Common, Group7, Group8 등)
            filename: 파일명
            format_type: 'JSON' 또는 'TEXT'
            test_mode: 테스트 모드 여부
        """
        self.storage = LocalFileBase(test_mode=test_mode)
        self.group = group
        self.filename = filename
        self.format_type = format_type
        self.DATA = None
        
        # 초기 데이터 로드
        self.load()
    
    def load(self):
        """파일에서 데이터 로드"""
        self.DATA = self.storage.openFile(self.group, self.filename, self.format_type)
        
        # GIST와 동일한 형식으로 변환
        if self.format_type == 'TEXT':
            # TEXT는 set으로 변환
            if isinstance(self.DATA, list):
                self.DATA = set(self.DATA)
            elif self.DATA == "":
                self.DATA = set()
            else:
                self.DATA = set()
        else:
            # JSON은 dict로
            if not isinstance(self.DATA, dict):
                self.DATA = {}
    
    def update(self):
        """변경사항을 파일에 저장"""
        if self.format_type == 'TEXT':
            # set을 list로 변환하여 저장
            data_to_save = list(self.DATA) if self.DATA else []
        else:
            # dict는 그대로
            data_to_save = self.DATA if self.DATA else {}
        
        return self.storage.uploadFile(self.group, self.filename, data_to_save, self.format_type)
    
    def edit(self, mode, *args):
        """데이터 편집 (GIST와 동일한 인터페이스)"""
        if self.format_type == 'TEXT':
            # TEXT 모드: edit(mode, text)
            if mode == '+' and len(args) >= 1:
                self.DATA.add(args[0])
            elif mode == '-' and len(args) >= 1:
                self.DATA.discard(args[0])
        else:
            # JSON 모드: edit(mode, key, value)
            if mode == '+' and len(args) >= 2:
                self.DATA[args[0]] = args[1]
            elif mode == '-' and len(args) >= 1:
                self.DATA.pop(args[0], None)
    
    def fetch_raw(self):
        """호환성을 위한 메서드 (로컬에서는 load와 동일)"""
        self.load()
        return self.DATA
    
    def fetch_data(self):
        """호환성을 위한 메서드 (로컬에서는 load와 동일)"""
        self.load()
        return self.DATA

# GIST 클래스를 흉내내는 팩토리 함수들
def TEXT(gist_id, filename, initial=True, test_mode=False):
    """GIST.TEXT와 동일한 인터페이스"""
    # Poke.py의 실제 사용 패턴에 맞춰 파일명 매핑
    mapping = {
        'Admin': ('Common', 'Common_admin'),
        'Group7': ('Group7', 'Group7_online'),
        'Group8': ('Group8', 'Group8_online')
    }
    
    if filename in mapping:
        group, fname = mapping[filename]
    else:
        # 기본값
        group = 'Common'
        fname = filename
    
    adapter = LocalFileAdapter(group, fname, 'TEXT', test_mode)
    return adapter

def JSON(gist_id, filename, initial=True, test_mode=False):
    """GIST.JSON과 동일한 인터페이스"""
    # Poke.py의 실제 사용 패턴에 맞춰 파일명 매핑
    mapping = {
        'Alliance': ('Common', 'Common_member'),
        'GodPack7': ('Group7', 'Group7_godpack'),
        'Code7': ('Group7', 'Group7_godpackCode'),
        'GodPack8': ('Group8', 'Group8_godpack'),
        'Code8': ('Group8', 'Group8_godpackCode')
    }
    
    if filename in mapping:
        group, fname = mapping[filename]
    else:
        # 기본값
        group = 'Common'
        fname = filename
    
    adapter = LocalFileAdapter(group, fname, 'JSON', test_mode)
    return adapter