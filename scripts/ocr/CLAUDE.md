# OCR 스크립트 디렉토리

이 디렉토리는 DETECT 채널의 이미지에서 사용자 정보를 추출하는 OCR 시스템 관련 스크립트를 포함합니다.

## 디렉토리 구조

```
scripts/ocr/
├── test_ocr_comparison.py    # OCR 엔진 비교 테스트
├── requirements_ocr.txt      # OCR 라이브러리 의존성
├── process_ocr_queue.py      # OCR 워커 프로세스 (구현 예정)
└── results/                  # 테스트 결과 저장
    ├── comparison_report.md  # 비교 테스트 리포트
    └── comparison_data.json  # 테스트 원시 데이터
```

## 파일 설명

### test_ocr_comparison.py
- 3가지 OCR 엔진 (Tesseract, EasyOCR, PaddleOCR) 성능 비교
- FRIENDCODE 이미지에서 사용자명과 친구코드 추출
- 정확도, 처리 속도, 사용 편의성 평가
- 최적 엔진 선정을 위한 테스트

### requirements_ocr.txt
- OCR 엔진별 의존성 라이브러리
- 이미지 처리 관련 라이브러리
- 버전 제약 없이 최신 버전 사용

### process_ocr_queue.py (구현 예정)
- 파일 기반 큐 시스템의 워커 프로세스
- 비동기 OCR 처리
- 봇과 독립적으로 실행

## 사용 방법

1. **의존성 설치**
   ```bash
   pip install -r requirements_ocr.txt
   ```

2. **Tesseract 설치 (macOS)**
   ```bash
   brew install tesseract
   ```

3. **OCR 엔진 비교 테스트 실행**
   ```bash
   python test_ocr_comparison.py
   ```

4. **결과 확인**
   - `results/comparison_report.md`: 비교 분석 리포트
   - `results/comparison_data.json`: 상세 테스트 데이터

## 테스트 이미지
- `data_test/DATA_DETECT/media/`: 기존 테스트 이미지
- `data_test/DATA_DETECT/media2/`: 최신 테스트 이미지
- FRIENDCODE 패턴의 이미지만 사용

## 주의사항
- OCR은 CPU 집약적 작업이므로 별도 프로세스로 실행 권장
- 이미지 품질에 따라 정확도가 달라질 수 있음
- 친구코드는 정규식으로 재검증 필요