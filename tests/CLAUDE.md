# tests 디렉토리 가이드

테스트 코드 및 테스트용 봇 변형들이 위치한 디렉토리입니다.

## 테스트 파일별 상세 정보

### Poke_test.py
- **기능**: Poke.py의 테스트 버전
- **특징**: 
  - 테스트 모드 플래그 포함
  - 디버그 출력 강화
  - 실제 데이터 미반영 옵션

### Poke_local.py
- **기능**: Poke.py의 로컬 파일 버전
- **용도**: Gist → LocalFile 마이그레이션 테스트
- **특징**: LocalFileAdapter 사용

### test_adapter.py
- **기능**: LocalFileAdapter 단위 테스트
- **테스트 항목**:
  - 파일 읽기/쓰기
  - Gist 인터페이스 호환성
  - 에러 처리

### test_local_system.py
- **기능**: 전체 로컬 시스템 통합 테스트
- **테스트 항목**:
  - 디렉토리 구조
  - 파일 권한
  - 데이터 무결성

## 실행 방법
```bash
python -m pytest tests/  # 전체 테스트
python tests/Poke_test.py  # 개별 봇 테스트
```

## 주의사항
- 테스트 실행 시 별도 환경 변수 사용
- 실제 Discord 서버에 영향 없도록 주의
- 테스트 데이터는 `data_test/` 사용