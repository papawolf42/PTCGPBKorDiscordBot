# OCR 시스템 구현 계획

## 개요
DETECT 채널에서 2개의 이미지가 첨부된 경우, 두 번째 이미지(계정 정보)에서 사용자명과 친구코드를 OCR로 추출하는 시스템 구현

## 목표
- 텍스트 메시지에 친구코드가 없거나 잘못된 경우 OCR로 보완
- 비동기 처리로 봇 성능 영향 최소화
- 3가지 OCR 엔진 비교 후 최적 엔진 선택

## 📋 단계별 구현 계획

### 🎯 Phase 1: OCR 엔진 독립 테스트 및 비교

#### 1.1 테스트 환경 구성
```
scripts/ocr/
├── test_ocr_comparison.py    # 3가지 OCR 엔진 비교 테스트
├── requirements_ocr.txt       # OCR 라이브러리 의존성
└── results/                   # 테스트 결과 저장
    └── comparison_report.md
```

#### 1.2 테스트 대상
- **Tesseract**: Google의 오픈소스 OCR
- **EasyOCR**: 딥러닝 기반, 다국어 지원
- **PaddleOCR**: Baidu의 딥러닝 OCR

#### 1.3 테스트 항목
- 정확도: 사용자명, 친구코드 추출 정확도
- 처리 속도: 이미지당 처리 시간
- 리소스 사용량: CPU/메모리
- 설치 및 사용 편의성

#### 1.4 테스트 이미지
FRIENDCODE 이미지 10개 선정 (다양한 사용자명 패턴 포함)
- 영문만: MinMin5650
- 영문+숫자: laff155, RKLB1
- 특수문자 포함 케이스

### 🎯 Phase 2: OCR 모듈 개발

#### 2.1 모듈 구조
```
src/modules/
├── OCRProcessor.py           # 메인 OCR 처리 클래스
└── ocr_engines/              # OCR 엔진 래퍼
    ├── __init__.py
    ├── base_engine.py        # 추상 베이스 클래스
    ├── tesseract_engine.py
    ├── easyocr_engine.py
    └── paddleocr_engine.py
```

#### 2.2 OCRProcessor 인터페이스
```python
class OCRProcessor:
    def __init__(self, engine='best'):
        """최적 엔진으로 초기화"""
        
    def process_image(self, image_path):
        """이미지에서 정보 추출"""
        return {
            'name': 'extracted_name',
            'friend_code': 'xxxx-xxxx-xxxx-xxxx',
            'confidence': 0.95,
            'engine_used': 'tesseract'
        }
        
    def add_to_queue(self, message_id, image_url, metadata):
        """비동기 처리를 위한 큐 추가"""
        
    def check_completed(self):
        """완료된 OCR 결과 확인"""
```

### 🎯 Phase 3: 파일 기반 큐 시스템

#### 3.1 디렉토리 구조
```
data/
├── ocr_queue/               # 처리 대기
│   └── {timestamp}_{message_id}.json
├── ocr_processing/          # 처리 중 (락 방지)
│   └── {timestamp}_{message_id}.json
└── ocr_completed/           # 처리 완료
    └── {timestamp}_{message_id}_result.json
```

#### 3.2 큐 파일 형식
**대기 큐 (ocr_queue/{timestamp}_{message_id}.json)**
```json
{
    "message_id": "1234567890",
    "timestamp": "2025-06-07T10:00:00",
    "image_url": "https://cdn.discord.com/attachments/.../image.png",
    "metadata": {
        "type": "godpack",
        "text_parsing_result": {
            "name": "partial_name",
            "friend_code": null
        },
        "channel_id": "1234567890",
        "user_id": "0987654321"
    }
}
```

**완료 결과 (ocr_completed/{timestamp}_{message_id}_result.json)**
```json
{
    "message_id": "1234567890",
    "ocr_result": {
        "name": "MinMin5650",
        "friend_code": "5536-3193-4550-0719",
        "confidence": 0.95,
        "engine": "tesseract"
    },
    "processing_time": 2.5,
    "completed_at": "2025-06-07T10:00:02.5"
}
```

### 🎯 Phase 4: OCR 워커 프로세스

#### 4.1 워커 스크립트
```python
# scripts/ocr/process_ocr_queue.py
while True:
    # 1. 가장 오래된 대기 파일 선택
    # 2. processing 폴더로 이동 (락)
    # 3. 이미지 다운로드
    # 4. OCR 처리
    # 5. 결과 저장
    # 6. 정리
    time.sleep(1)
```

#### 4.2 에러 처리
- 재시도 로직 (최대 3회)
- 실패 시 fallback (텍스트 파싱 결과 사용)
- 타임아웃 설정 (30초)

### 🎯 Phase 5: GISTAdapter 통합

#### 5.1 수정 사항
```python
# GISTAdapter.found_GodPack() 수정
if len(message.attachments) == 2:
    # OCR 큐에 추가
    await self.ocr_processor.add_to_queue(
        message_id=message.id,
        image_url=message.attachments[1].url,
        metadata={
            "type": "godpack",
            "text_result": text_parsing_result
        }
    )
```

### 🎯 Phase 6: Poke.py 통합

#### 6.1 OCR 결과 확인 루프
```python
@tasks.loop(seconds=5)
async def check_ocr_results(self):
    """OCR 완료 결과 확인 및 포스팅 업데이트"""
    completed = await self.ocr_processor.check_completed()
    for result in completed:
        # 기존 포스팅 찾기
        # OCR 결과로 정보 업데이트
        # 포럼 메시지 수정
```

## 📊 예상 처리 흐름

```
1. DETECT 채널 메시지 (2개 이미지)
   ↓
2. GISTAdapter.found_GodPack()
   ├─ 텍스트 파싱 (즉시 반환)
   └─ OCR 큐 추가 (비동기)
   ↓
3. 포럼 포스팅 (텍스트 파싱 결과)
   ↓
4. OCR 워커 프로세스 (별도 실행)
   └─ 이미지 다운로드 → OCR → 결과 저장
   ↓
5. Poke.py check_ocr_results() (5초마다)
   └─ 완료된 OCR 확인 → 포스팅 업데이트
```

## 🚀 구현 일정

1. **Day 1**: OCR 엔진 비교 테스트
2. **Day 2**: 최적 엔진 선택 및 OCRProcessor 개발
3. **Day 3**: 파일 기반 큐 시스템 구현
4. **Day 4**: 워커 프로세스 개발 및 테스트
5. **Day 5**: GISTAdapter/Poke.py 통합

## ⚠️ 주의사항

1. **성능**: OCR은 CPU 집약적이므로 별도 프로세스로 실행
2. **정확도**: 친구코드는 정규식으로 재검증
3. **에러 처리**: OCR 실패 시 텍스트 파싱 결과 유지
4. **리소스 관리**: 완료된 파일은 주기적으로 정리

## 📈 성공 지표

- OCR 정확도 95% 이상
- 처리 시간 5초 이내
- 봇 성능 영향 최소화
- 안정적인 에러 처리