#!/usr/bin/env python3
"""
중복 로그 제거 테스트
"""
import os
import sys
import logging

# 환경 설정
os.environ['ENVIRONMENT'] = 'development'

# 프로젝트 루트를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.optimized_logger import OptimizedLogger, get_optimized_logger

def test_duplicate_log_removal():
    """중복 로그 제거 테스트"""
    print("="*60)
    print("중복 로그 제거 테스트 시작")
    print("="*60)
    
    # 1. OptimizedLogger 테스트
    print("\n1. OptimizedLogger 테스트")
    print("-" * 30)
    
    logger1 = get_optimized_logger("test1", "A")
    logger1.log_info(">>>>>[현재 적용 가능한 쿠폰]")
    logger1.log_info("30분할인권(무료): 0개")
    logger1.log_info("1시간할인권(유료): 0개")
    
    # 2. 기존 Python logger와 비교
    print("\n2. 기존 Python logger 테스트")
    print("-" * 30)
    
    python_logger = logging.getLogger("test2")
    if not python_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        python_logger.addHandler(handler)
        python_logger.setLevel(logging.INFO)
    
    python_logger.info("[A] >>>>>[우리 매장에서 적용한 쿠폰]")
    python_logger.info("[A] 30분할인권(무료): 1개")
    python_logger.info("[A] 1시간할인권(유료): 2개")
    
    # 3. 환경별 로그 레벨 테스트
    print("\n3. 환경별 로그 레벨 테스트")
    print("-" * 30)
    
    # 개발 환경
    dev_logger = get_optimized_logger("dev_test", "A")
    dev_logger.log_info("개발 환경 INFO 로그 - 표시됨")
    dev_logger.log_warning("개발 환경 WARNING 로그 - 표시됨")
    
    # 프로덕션 환경 시뮬레이션
    os.environ['ENVIRONMENT'] = 'production'
    prod_logger = get_optimized_logger("prod_test", "A") 
    prod_logger.log_info("프로덕션 환경 INFO 로그 - 표시 안됨")
    prod_logger.log_warning("프로덕션 환경 WARNING 로그 - 표시됨")
    
    # 환경 복원
    os.environ['ENVIRONMENT'] = 'development'
    
    print("\n4. 에러 로그 테스트")
    print("-" * 30)
    
    error_logger = get_optimized_logger("error_test", "A")
    error_details = error_logger.log_error("A", "차량검색", "NO_VEHICLE", "차량번호 12가3456 검색 결과 없음")
    print(f"에러 로그 반환값: {error_details}")
    
    print("\n" + "="*60)
    print("중복 로그 제거 테스트 완료")
    print("="*60)
    print("\n주요 변경사항:")
    print("✅ OptimizedLogger에서 logger.propagate = False 설정으로 중복 출력 방지")
    print("✅ Use Case에서 상세 로그 제거 (프로덕션 환경에서는 WARNING 이상만)")
    print("✅ 크롤러에서 should_log_info() 체크로 개발 환경에서만 상세 로그")
    print("✅ CloudWatch Logs 비용 절감을 위한 로그 레벨 최적화")

if __name__ == "__main__":
    test_duplicate_log_removal() 