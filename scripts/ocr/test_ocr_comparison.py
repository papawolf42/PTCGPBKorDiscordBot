#!/usr/bin/env python3
"""
OCR 엔진 비교 테스트 스크립트
Tesseract, EasyOCR, PaddleOCR 3가지 엔진의 성능을 비교합니다.
"""

import os
import sys
import time
import json
import re
import logging
import argparse
from datetime import datetime
from pathlib import Path
import traceback

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 로깅 설정
def setup_logging(debug=False):
    """로깅 설정"""
    log_dir = project_root / "logs" / "ocr"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_level = logging.DEBUG if debug else logging.INFO
    log_file = log_dir / f"ocr_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 로깅 포맷 설정
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
    
    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.info(f"로그 파일: {log_file}")
    return logger

# 이미지 처리 라이브러리
try:
    from PIL import Image
    import cv2
    import numpy as np
except ImportError as e:
    print(f"필수 라이브러리가 설치되지 않았습니다: {e}")
    print("다음 명령어로 설치해주세요:")
    print("pip install -r requirements_ocr.txt")
    sys.exit(1)


class OCRTester:
    """OCR 엔진 테스터"""
    
    def __init__(self, debug=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.debug = debug
        self.results = []
        self.engines = {}
        self.test_images = []
        self._setup_test_images()
    
    def _setup_test_images(self):
        """테스트용 이미지 목록 설정"""
        # 다양한 사용자명 패턴을 포함한 이미지 선택
        # 일단 기존 3개는 수동으로 확인한 데이터
        test_cases = [
            # (파일명, 예상 사용자명, 예상 친구코드)
            ("20250420002302_1_FRIENDCODE_2_packs-659CE.png", "laff155", "6855-9066-8316-7259"),
            ("20250606130641_1_FRIENDCODE_1_packs-08C91.png", "MinMin5650", "5536-3193-4550-0719"),
            ("20250606214453_1_FRIENDCODE_2_packs-ED9A8.png", "RKLB1", "5494-0377-0130-0243"),
        ]
        
        # 추가 테스트 케이스를 위해 더 많은 이미지 수집
        # 예상값은 OCR 결과를 보면서 수동으로 추가해야 함
        additional_images = [
            "20250606232040_4_FRIENDCODE_1_packs-739DE.png",
            "20250606155242_1_FRIENDCODE_1_packs-F513E.png", 
            "20250606114640_3_FRIENDCODE_2_packs-4C292.png",
            "20250606194115_3_FRIENDCODE_2_packs-ECD1C.png",
            "20250606224723_4_FRIENDCODE_2_packs-C9EC1.png",
            "20250606215523_4_FRIENDCODE_1_packs-2BB20.png",
            "20250606144629_3_FRIENDCODE_1_packs-7166F.png",
            "20250606222525_4_FRIENDCODE_1_packs-20B4F.png",
            "20250606155223_4_FRIENDCODE_1_packs-4E58B.png",
            "20250606224826_2_FRIENDCODE_2_packs-2DCE6.png",
            "20250606185245_1_FRIENDCODE_1_packs-4A065.png",
            "20250606220203_1_FRIENDCODE_2_packs-2DC13.png",
            "20250606222825_4_FRIENDCODE_1_packs-1EC66.png",
            "20250606192843_3_FRIENDCODE_2_packs-C4C30.png",
            "20250420013408_2_FRIENDCODE_4_packs-9EDAD.png",
            "20250421142109_1_FRIENDCODE_5_packs-8730D.png",
            "20250420103152_2_FRIENDCODE_4_packs-86A32.png",
            "20250420134217_6_FRIENDCODE_1_packs-1BE34.png",
            "20250420162935_1_FRIENDCODE_5_packs-A0105.png",
            "20250420080624_4_FRIENDCODE_5_packs-C4EAC.png",
            "20250420041403_7_FRIENDCODE_3_packs-9C8C4.png",
            "20250420055246_1_FRIENDCODE_3_packs-EE39D.png",
            "20250420202602_5_FRIENDCODE_4_packs-B44EF.png",
            "20250421150043_7_FRIENDCODE_5_packs-85AE5.png",
            "20250420062609_6_FRIENDCODE_1_packs-19D86.png",
            "20250420160247_4_FRIENDCODE_2_packs-8F2F3.png",
            "20250420030637_3_FRIENDCODE_1_packs-95067.png",
        ]
        
        # 일단 예상값 없이 이미지만 추가 (OCR 결과 확인용)
        for filename in additional_images:
            test_cases.append((filename, "UNKNOWN", "UNKNOWN"))
        
        # 실제 이미지 경로 확인
        media_dirs = [
            project_root / "DATA_DETECT" / "media",
            project_root / "DATA_DETECT" / "media2"
        ]
        
        for filename, expected_name, expected_code in test_cases:
            for media_dir in media_dirs:
                image_path = media_dir / filename
                if image_path.exists():
                    self.test_images.append({
                        'path': str(image_path),
                        'filename': filename,
                        'expected_name': expected_name,
                        'expected_code': expected_code
                    })
                    break
        
        self.logger.info(f"테스트 이미지 {len(self.test_images)}개 준비 완료")
        for img in self.test_images:
            self.logger.debug(f"  - {img['filename']}: {img['expected_name']} / {img['expected_code']}")
    
    def init_tesseract(self):
        """Tesseract OCR 초기화"""
        try:
            import pytesseract
            # Tesseract 실행 파일 경로 확인 (macOS)
            tesseract_paths = [
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract',
                '/usr/bin/tesseract'
            ]
            
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
            
            # 버전 확인
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract 버전: {version}")
            
            # 언어 데이터 확인
            langs = pytesseract.get_languages()
            self.logger.debug(f"Tesseract 사용 가능 언어: {langs}")
            
            self.engines['tesseract'] = pytesseract
            return True
        except Exception as e:
            self.logger.error(f"Tesseract 초기화 실패: {e}")
            self.logger.debug(f"스택 트레이스:\n{traceback.format_exc()}")
            self.logger.info("설치 방법: brew install tesseract")
            self.logger.info("한국어 데이터 설치: brew install tesseract-lang")
            return False
    
    def init_easyocr(self):
        """EasyOCR 초기화"""
        try:
            import easyocr
            # GPU 사용 가능 여부에 따라 설정
            reader = easyocr.Reader(['ko', 'en'], gpu=False)
            self.engines['easyocr'] = reader
            self.logger.info("EasyOCR 초기화 완료")
            return True
        except Exception as e:
            self.logger.error(f"EasyOCR 초기화 실패: {e}")
            self.logger.debug(f"스택 트레이스:\n{traceback.format_exc()}")
            return False
    
    def init_vision(self):
        """macOS Vision.framework 초기화"""
        try:
            # macOS 버전 확인
            import platform
            mac_version = platform.mac_ver()[0]
            if mac_version:
                major_version = int(mac_version.split('.')[0])
                if major_version < 12:  # Monterey 이전
                    self.logger.warning(f"macOS {mac_version}은 Vision OCR을 지원하지 않습니다. (Monterey 12.0 이상 필요)")
                    return False
            
            # PyObjC 임포트
            import Vision
            import Quartz
            from Foundation import NSURL
            
            self.engines['vision'] = {
                'Vision': Vision,
                'Quartz': Quartz,
                'NSURL': NSURL
            }
            self.logger.info("macOS Vision.framework 초기화 완료")
            self.logger.debug(f"macOS 버전: {mac_version}")
            
            return True
        except ImportError as e:
            self.logger.error("Vision.framework 초기화 실패: PyObjC가 설치되지 않았습니다.")
            self.logger.info("설치 방법: pip install pyobjc-framework-Vision pyobjc-framework-Quartz")
            return False
        except Exception as e:
            self.logger.error(f"Vision.framework 초기화 실패: {e}")
            self.logger.debug(f"스택 트레이스:\n{traceback.format_exc()}")
            return False
    
    def preprocess_image(self, image_path):
        """이미지 전처리"""
        # OpenCV로 이미지 읽기
        img = cv2.imread(image_path)
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 대비 증가
        enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(enhanced)
        
        return img, denoised
    
    def extract_info_from_text(self, text):
        """OCR 텍스트에서 사용자명과 친구코드 추출"""
        # 텍스트 정리
        text = text.replace('\n', ' ').strip()
        self.logger.debug(f"정리된 텍스트 (길이: {len(text)}): {text[:200]}...")
        
        # 친구코드 패턴 (4자리-4자리-4자리-4자리)
        # 더 유연한 패턴: -, ., *, 공백 등을 구분자로 허용
        code_pattern = r'\d{4}[-\.\*\s]?\d{4}[-\.\*\s]?\d{4}[-\.\*\s]?\d{4}'
        self.logger.debug(f"친구코드 정규식 패턴: {code_pattern}")
        code_match = re.search(code_pattern, text)
        
        friend_code = None
        if code_match:
            # 하이픈으로 정규화
            raw_code = code_match.group()
            friend_code = re.sub(r'[-\.\*\s]+', '-', raw_code)
            self.logger.debug(f"친구코드 매칭: {raw_code} -> {friend_code}")
        else:
            self.logger.debug("친구코드 매칭 실패")
        
        # 사용자명 추출 (휴리스틱)
        # "당신의 플레이어 정보" 이후, 친구코드 이전의 텍스트
        name = None
        name_patterns = [
            r'정보\s+([A-Za-z0-9]+)',  # 영숫자 사용자명
            r'플레이어\s+([A-Za-z0-9]+)',
            r'([A-Za-z0-9]+)\s+친구',
            # Tesseract용 추가 패턴
            r'^([A-Za-z0-9]+)$',  # 단독 라인에 있는 사용자명
            r'([A-Za-z0-9]{3,20})',  # 3-20자리 영숫자
        ]
        
        for pattern in name_patterns:
            self.logger.debug(f"사용자명 패턴 시도: {pattern}")
            match = re.search(pattern, text)
            if match:
                name = match.group(1)
                self.logger.debug(f"사용자명 매칭 성공: {name}")
                break
            else:
                self.logger.debug(f"패턴 {pattern} 매칭 실패")
        
        return {
            'name': name,
            'friend_code': friend_code,
            'raw_text': text[:200]  # 디버깅용
        }
    
    def test_tesseract(self, image_path):
        """Tesseract OCR 테스트"""
        if 'tesseract' not in self.engines:
            return None
        
        start_time = time.time()
        try:
            pytesseract = self.engines['tesseract']
            img, processed = self.preprocess_image(image_path)
            
            # 영어만으로 OCR 수행 (한국어가 오히려 방해될 수 있음)
            text = pytesseract.image_to_string(processed, lang='eng')
            
            elapsed_time = time.time() - start_time
            result = self.extract_info_from_text(text)
            result['time'] = elapsed_time
            result['engine'] = 'tesseract'
            
            self.logger.debug(f"Tesseract OCR 원본 텍스트:\n{text}")
            
            return result
        except Exception as e:
            self.logger.error(f"Tesseract 오류: {e}")
            self.logger.debug(f"스택 트레이스:\n{traceback.format_exc()}")
            return None
    
    def test_easyocr(self, image_path):
        """EasyOCR 테스트"""
        if 'easyocr' not in self.engines:
            return None
        
        start_time = time.time()
        try:
            reader = self.engines['easyocr']
            
            # OCR 수행
            results = reader.readtext(image_path)
            
            # 텍스트 합치기
            text = ' '.join([item[1] for item in results])
            
            elapsed_time = time.time() - start_time
            result = self.extract_info_from_text(text)
            result['time'] = elapsed_time
            result['engine'] = 'easyocr'
            
            self.logger.debug(f"EasyOCR 결과 개수: {len(results)}")
            self.logger.debug(f"EasyOCR 원본 텍스트:\n{text}")
            
            return result
        except Exception as e:
            self.logger.error(f"EasyOCR 오류: {e}")
            self.logger.debug(f"스택 트레이스:\n{traceback.format_exc()}")
            return None
    
    def test_vision(self, image_path):
        """macOS Vision.framework 테스트"""
        if 'vision' not in self.engines:
            return None
        
        start_time = time.time()
        try:
            Vision = self.engines['vision']['Vision']
            Quartz = self.engines['vision']['Quartz']
            NSURL = self.engines['vision']['NSURL']
            
            # 이미지 로드
            input_url = NSURL.fileURLWithPath_(image_path)
            input_image = Quartz.CIImage.imageWithContentsOfURL_(input_url)
            
            # 텍스트 인식 요청 생성
            request = Vision.VNRecognizeTextRequest.alloc().init()
            request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            request.setRecognitionLanguages_(['en-US', 'ko-KR'])  # 영어와 한국어
            request.setUsesLanguageCorrection_(True)
            
            # 이미지 핸들러 생성 및 요청 수행
            handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(
                input_image, None
            )
            
            success = handler.performRequests_error_([request], None)
            
            if not success:
                self.logger.error("Vision OCR 요청 실패")
                return None
            
            # 결과 추출
            text_list = []
            observations = request.results()
            
            self.logger.debug(f"Vision 인식 결과: {len(observations)}개 텍스트 블록")
            
            for observation in observations:
                text = observation.text()
                confidence = observation.confidence()
                text_list.append(text)
                self.logger.debug(f"  텍스트: '{text}' (신뢰도: {confidence:.2f})")
            
            full_text = ' '.join(text_list)
            
            elapsed_time = time.time() - start_time
            result = self.extract_info_from_text(full_text)
            result['time'] = elapsed_time
            result['engine'] = 'vision'
            
            self.logger.debug(f"Vision 원본 텍스트:\n{full_text}")
            
            return result
        except Exception as e:
            self.logger.error(f"Vision 오류: {e}")
            self.logger.debug(f"스택 트레이스:\n{traceback.format_exc()}")
            return None
    
    def run_comparison(self):
        """모든 엔진으로 비교 테스트 실행"""
        self.logger.info("\n=== OCR 엔진 비교 테스트 시작 ===\n")
        
        # 엔진 초기화
        self.logger.info("1. OCR 엔진 초기화")
        tesseract_ok = self.init_tesseract()
        easyocr_ok = self.init_easyocr()
        vision_ok = self.init_vision()
        
        self.logger.info(f"초기화 결과 - Tesseract: {tesseract_ok}, EasyOCR: {easyocr_ok}, Vision: {vision_ok}")
        
        if not self.engines:
            self.logger.error("초기화된 OCR 엔진이 없습니다!")
            return
        
        # 각 이미지에 대해 테스트
        self.logger.info(f"\n2. {len(self.test_images)}개 이미지 테스트 시작\n")
        
        for img_info in self.test_images:
            self.logger.info(f"\n테스트 이미지: {img_info['filename']}")
            self.logger.info(f"예상값 - 이름: {img_info['expected_name']}, 코드: {img_info['expected_code']}")
            self.logger.debug(f"이미지 경로: {img_info['path']}")
            
            results = {
                'image': img_info['filename'],
                'expected': {
                    'name': img_info['expected_name'],
                    'code': img_info['expected_code']
                },
                'results': {}
            }
            
            # 각 엔진으로 테스트
            for engine_name, test_func in [
                ('tesseract', self.test_tesseract),
                ('easyocr', self.test_easyocr),
                ('vision', self.test_vision)
            ]:
                if engine_name in self.engines:
                    self.logger.info(f"\n  {engine_name} 테스트 중...")
                    result = test_func(img_info['path'])
                    if result:
                        results['results'][engine_name] = result
                        name_match = result.get('name') == img_info['expected_name']
                        code_match = result.get('friend_code') == img_info['expected_code']
                        
                        self.logger.info(f"    이름: {result.get('name', 'None')} {'✅' if name_match else '❌'}")
                        self.logger.info(f"    코드: {result.get('friend_code', 'None')} {'✅' if code_match else '❌'}")
                        self.logger.info(f"    시간: {result.get('time', 0):.2f}초")
                    else:
                        self.logger.warning(f"    {engine_name} 결과 없음")
            
            self.results.append(results)
    
    def generate_report(self):
        """비교 결과 리포트 생성"""
        report_path = Path(__file__).parent / "results" / "comparison_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# OCR 엔진 비교 결과\n\n")
            f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 요약 통계
            f.write("## 요약\n\n")
            
            engine_stats = {}
            for engine in ['tesseract', 'easyocr', 'vision']:
                engine_stats[engine] = {
                    'name_correct': 0,
                    'code_correct': 0,
                    'total_time': 0,
                    'count': 0
                }
            
            # 통계 계산
            for result in self.results:
                for engine, data in result['results'].items():
                    stats = engine_stats[engine]
                    stats['count'] += 1
                    stats['total_time'] += data.get('time', 0)
                    
                    if data.get('name') == result['expected']['name']:
                        stats['name_correct'] += 1
                    if data.get('friend_code') == result['expected']['code']:
                        stats['code_correct'] += 1
            
            # 통계 테이블
            f.write("| 엔진 | 이름 정확도 | 코드 정확도 | 평균 처리시간 |\n")
            f.write("|------|------------|------------|-------------|\n")
            
            for engine, stats in engine_stats.items():
                if stats['count'] > 0:
                    name_acc = stats['name_correct'] / stats['count'] * 100
                    code_acc = stats['code_correct'] / stats['count'] * 100
                    avg_time = stats['total_time'] / stats['count']
                    f.write(f"| {engine} | {name_acc:.1f}% | {code_acc:.1f}% | {avg_time:.2f}초 |\n")
            
            # 상세 결과
            f.write("\n## 상세 결과\n\n")
            
            for result in self.results:
                f.write(f"### {result['image']}\n\n")
                f.write(f"**예상값**: 이름={result['expected']['name']}, 코드={result['expected']['code']}\n\n")
                
                for engine, data in result['results'].items():
                    f.write(f"#### {engine}\n")
                    f.write(f"- 추출된 이름: {data.get('name', 'None')}")
                    if data.get('name') == result['expected']['name']:
                        f.write(" ✅")
                    else:
                        f.write(" ❌")
                    f.write("\n")
                    
                    f.write(f"- 추출된 코드: {data.get('friend_code', 'None')}")
                    if data.get('friend_code') == result['expected']['code']:
                        f.write(" ✅")
                    else:
                        f.write(" ❌")
                    f.write("\n")
                    
                    f.write(f"- 처리 시간: {data.get('time', 0):.2f}초\n")
                    f.write(f"- 원본 텍스트: `{data.get('raw_text', '')[:100]}...`\n\n")
            
            # 결론
            f.write("\n## 결론 및 권장사항\n\n")
            
            # 최고 성능 엔진 찾기
            best_engine = None
            best_score = 0
            
            for engine, stats in engine_stats.items():
                if stats['count'] > 0:
                    # 정확도와 속도를 고려한 점수 (정확도 중심)
                    score = (stats['name_correct'] + stats['code_correct']) / (2 * stats['count'])
                    if score > best_score:
                        best_score = score
                        best_engine = engine
            
            if best_engine:
                f.write(f"**권장 OCR 엔진**: {best_engine}\n\n")
                f.write("선정 이유:\n")
                stats = engine_stats[best_engine]
                f.write(f"- 이름 정확도: {stats['name_correct']}/{stats['count']}\n")
                f.write(f"- 코드 정확도: {stats['code_correct']}/{stats['count']}\n")
                f.write(f"- 평균 처리시간: {stats['total_time']/stats['count']:.2f}초\n")
        
        self.logger.info(f"\n리포트 생성 완료: {report_path}")
        
        # JSON 형식으로도 저장
        json_path = Path(__file__).parent / "results" / "comparison_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)


def main():
    """메인 실행 함수"""
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='OCR 엔진 비교 테스트')
    parser.add_argument('--debug', '-d', action='store_true', help='디버그 모드 활성화')
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging(debug=args.debug)
    
    tester = OCRTester(debug=args.debug)
    
    if not tester.test_images:
        logging.error("테스트할 이미지가 없습니다!")
        return
    
    tester.run_comparison()
    tester.generate_report()


if __name__ == "__main__":
    main()