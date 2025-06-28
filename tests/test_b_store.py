"""
B 매장 테스트 - 실제 검증된 구조 테스트
"""
import asyncio
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.domain.stores.b_store import BStore
from infrastructure.config.config_b import CONFIG_B
from shared.utils.logger import setup_logger


async def test_b_store():
    """B 매장 전체 프로세스 테스트"""
    logger = setup_logger("test_b_store")
    
    try:
        # 테스트용 차량번호 (실제 존재하는 차량번호로 변경 필요)
        test_car_number = "12가3456"
        
        logger.info(f"🧪 B 매장 테스트 시작 - 차량번호: {test_car_number}")
        
        # B 매장 객체 생성
        b_store = BStore(CONFIG_B)
        
        # 전체 프로세스 실행
        result = await b_store.run(test_car_number)
        
        if result:
            logger.info("[성공] B 매장 테스트 성공")
        else:
            logger.error("[실패] B 매장 테스트 실패")
        
        return result
        
    except Exception as e:
        logger.error(f"[실패] B 매장 테스트 중 오류: {str(e)}")
        return False


async def test_b_discount_rule():
    """B 매장 할인 규칙 테스트"""
    logger = setup_logger("test_b_discount_rule")
    
    try:
        from core.domain.rules.b_discount_rule import BDiscountRule
        
        logger.info("🧪 B 매장 할인 규칙 테스트 시작")
        
        rule = BDiscountRule()
        
        # 테스트 케이스 1: 아무 쿠폰도 적용되지 않은 상태 (평일)
        my_history = {}
        total_history = {}
        discount_info = {'PAID_30MIN': 5}  # 유료 30분할인 5개 보유
        
        result = rule.decide_coupon_to_apply(my_history, total_history, discount_info)
        logger.info(f"테스트 케이스 1 결과: {result}")
        
        # 테스트 케이스 2: 일부 쿠폰이 이미 적용된 상태
        my_history = {'PAID_30MIN': 2}  # 이미 30분 x 2 = 60분 적용됨
        total_history = {'PAID_30MIN': 3, 'FREE_1HOUR': 1}
        discount_info = {'PAID_30MIN': 3}  # 유료 30분할인 3개 보유
        
        result = rule.decide_coupon_to_apply(my_history, total_history, discount_info)
        logger.info(f"테스트 케이스 2 결과: {result}")
        
        logger.info("[성공] B 매장 할인 규칙 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"[실패] B 매장 할인 규칙 테스트 중 오류: {str(e)}")
        return False


if __name__ == "__main__":
    async def main():
        # 1. 할인 규칙 테스트
        await test_b_discount_rule()
        
        print("\n" + "="*50 + "\n")
        
        # 2. 전체 프로세스 테스트 (실제 웹사이트 접속)
        await test_b_store()
    
    asyncio.run(main()) 