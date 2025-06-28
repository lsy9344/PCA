"""
B 매장 수정된 로직 테스트 스크립트
- 검색 상태 유지 체크박스 확인 및 활성화
- 정확한 쿠폰 적용 개수 계산
- A 매장과 동일한 포맷의 로그 출력
"""
import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from infrastructure.config.config_manager import ConfigManager
from playwright.async_api import async_playwright
from infrastructure.web_automation.store_crawlers.b_store_crawler import BStoreCrawler
from core.domain.rules.b_discount_rule import BDiscountRule
import logging

## 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_b_store_updated():
    """B 매장 업데이트된 기능 테스트"""
    
    # 설정 로드
    config_manager = ConfigManager()
    b_config = config_manager.get_store_config("B")
    
    # B 매장 크롤러 초기화
    crawler = BStoreCrawler(b_config)
    
    async with async_playwright() as p:
        # 브라우저 실행 (headful 모드로 실행하여 실제 동작 확인)
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        try:
            logger.info("[시작] B 매장 업데이트된 자동화 테스트 시작")
            
            # 1. 로그인 테스트 (검색 상태 유지 체크박스 포함)
            logger.info("\n=== 1단계: 로그인 및 검색 상태 유지 체크박스 설정 ===")
            login_success = await crawler.login(page)
            if not login_success:
                raise Exception("로그인 실패")
            
            # 로그인 후 체크박스 상태 확인
            logger.info("[성공] 로그인 완료 - 검색 상태 유지 체크박스가 자동으로 설정되었는지 확인")
            
            # 2. 존재하는 차량번호로 검색 테스트
            logger.info("\n=== 2단계: 존재하는 차량번호 검색 테스트 ===")
            existing_car = "1234"  # 존재하는 차량번호 (테스트용)
            search_success = await crawler.search_car(page, existing_car)
            if search_success:
                logger.info(f"[성공] 차량번호 '{existing_car}' 검색 성공")
                
                # 3. 쿠폰 이력 조회 및 적용 테스트
                logger.info("\n=== 3단계: 쿠폰 이력 조회 및 적용 ===")
                my_history, total_history, discount_info = await crawler.get_coupon_history(page)
                
                # 할인 규칙 적용
                discount_rule = BDiscountRule()
                coupons_to_apply = discount_rule.decide_coupon_to_apply(my_history, total_history, discount_info)
                
                if coupons_to_apply:
                    logger.info(f"[보유] 적용할 쿠폰: {coupons_to_apply}")
                    apply_success = await crawler.apply_coupons(page, coupons_to_apply)
                    if apply_success:
                        logger.info("[성공] 쿠폰 적용 성공")
                    else:
                        logger.warning("[경고] 쿠폰 적용 실패")
                else:
                    logger.info("[정보] 적용할 쿠폰이 없습니다")
            else:
                logger.warning(f"[경고] 차량번호 '{existing_car}' 검색 실패")
       
        finally:
            # 사용자가 결과를 확인할 수 있도록 잠시 대기
            logger.info("⏱️ 10초 후 브라우저를 닫습니다...")
            await asyncio.sleep(10)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_b_store_updated()) 