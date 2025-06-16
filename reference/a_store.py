"""
A 매장 구현체
"""
from datetime import datetime
from playwright.async_api import TimeoutError
from .base_store import BaseStore
from config.global_config import STORE_CONFIGS, PLAYWRIGHT_CONFIG, TELEGRAM_CONFIG
from utils.telegram_notifier import TelegramNotifier
from utils.logger import setup_logger
from discount_rules.a_discount import ADiscountRule
import re
from typing import Dict

logger = setup_logger(__name__)

class AStore(BaseStore):
    """A 매장 구현체"""
    
    def __init__(self):
        super().__init__()
        self.config = STORE_CONFIGS["A"]
        self.telegram = TelegramNotifier(
            TELEGRAM_CONFIG["BOT_TOKEN"],
            TELEGRAM_CONFIG["CHAT_ID"]
        )
        self.discount_rule = ADiscountRule()  # A 매장 전용 쿠폰 규칙 사용
        
    async def login(self) -> bool:
        """로그인 수행 (팝업 처리 포함)"""
        try:
            # 웹사이트 접속
            await self.page.goto(self.config["WEBSITE_URL"])
            logger.info("[시작] A 매장 자동화 시작")
            
            # 1. 인트로 팝업 닫기
            try:
                await self.page.click("#skip")
                logger.info("[팝업처리] 인트로 팝업 닫기 성공")
            except Exception as e:
                logger.error(f"[팝업처리] 인트로 팝업 닫기 실패: {str(e)}")

            # 2. 공지 팝업 닫기
            try:
                await self.page.click("#popupCancel")
                logger.info("[팝업처리] 공지 팝업 닫기 성공")
            except Exception as e:
                logger.error(f"[팝업처리] 공지 팝업 닫기 실패: {str(e)}")
            
            # 로그인 폼 입력
            await self.page.fill("#id", self.config["LOGIN"]["USERNAME"])
            await self.page.fill("#password", self.config["LOGIN"]["PASSWORD"])
            await self.page.click("#login")
            
            # 로그인 성공 확인 (차량번호 입력란이 보이는지)
            await self.page.wait_for_selector("#carNumber", timeout=PLAYWRIGHT_CONFIG["TIMEOUT"])
            logger.info("[로그인] 로그인 성공")
            
            # 로그인 성공 후 팝업 처리
            try:
                await self.page.click('#gohome')
                logger.info("[로그인 후] 첫 번째 팝업 닫기 버튼 클릭 성공")
            except Exception as e:
                logger.error(f"[로그인 후] #gohome 버튼 클릭 실패: {str(e)}")
                
            try:
                await self.page.click('#start')
                logger.info("[로그인 후] 두 번째 팝업 닫기 버튼 클릭 성공")
            except Exception as e:
                logger.error(f"[로그인 후] #start 버튼 클릭 실패: {str(e)}")
                
            return True
            
        except TimeoutError:
            error_msg = "로그인 실패: 차량번호 입력란이 나타나지 않음"
            logger.error(f"[로그인] {error_msg}")
            return False
        except Exception as e:
            error_msg = f"로그인 실패: {str(e)}"
            logger.error(f"[로그인] {error_msg}")
            return False
            
    async def search_car(self, car_number: str) -> bool:
        """차량 검색"""
        try:
            # 차량번호 입력
            await self.page.fill("#carNumber", car_number)
            logger.info('[차량검색] 차량 번호 입력 성공')
            
            # 검색 버튼 클릭 (여러 셀렉터 시도)
            try:
                await self.page.click('button[name="search"]')
            except:
                try:
                    await self.page.click('.btn-search')
                except:
                    await self.page.click('button:has-text("검색")')
            
            # 검색 결과 대기
            await self.page.wait_for_timeout(1000)  # 결과 로딩 대기
            
            # [추가] #parkName의 텍스트가 '검색된 차량이 없습니다.'인지 확인
            try:
                park_name_elem = self.page.locator('#parkName')
                if await park_name_elem.count() > 0:
                    park_name_text = await park_name_elem.inner_text()
                    if '검색된 차량이 없습니다.' in park_name_text:
                        error_msg = '[차량검색] #parkName: 검색된 차량이 없습니다.'
                        logger.error(error_msg)
                        await self.telegram.send_error(error_msg, car_number)
                        return False
            except Exception as e:
                logger.error(f'[차량검색] #parkName 텍스트 확인 실패: {str(e)}')
            
            # 기존: 검색 결과 확인
            no_result = self.page.locator('text="검색된 차량이 없습니다"')
            if await no_result.count() > 0:
                error_msg = "검색된 차량이 없습니다"
                logger.error(f"[차량검색] {error_msg}")
                await self.telegram.send_error(error_msg, car_number)
                return False
                
            # 차량 선택 버튼 클릭
            try:
                # 버튼을 우선적으로 클릭
                await self.page.click('#next')
                logger.info('[차량검색] 차량 선택 버튼 클릭 성공')
                # 다음 페이지 로딩을 위해 5초 대기
                await self.page.wait_for_timeout(5000)  # 5000ms = 5초
            except Exception as e1:
                try:
                    await self.page.click('button:has-text("차량 선택")')
                    logger.info('[차량검색] button:has-text("차량 선택") 버튼 클릭 성공')
                    # 다음 페이지 로딩을 위해 3초 대기
                    await self.page.wait_for_timeout(3000)  # 3000ms = 3초
                except Exception as e2:
                    error_msg = f'[차량검색] 차량 선택 버튼 클릭 실패: #next: {str(e1)}, has-text: {str(e2)}'
                    logger.error(error_msg)
                    await self.telegram.send_error(error_msg, car_number)
                    return False
            
            logger.info(f"[차량검색] 차량번호 {car_number} 검색 및 선택 후 페이지 로딩 성공")
            return True
            
        except Exception as e:
            error_msg = f"차량 검색 실패: {str(e)}"
            logger.error(f"[차량검색] {error_msg}")
            await self.telegram.send_error(error_msg, car_number)
            return False
            
    async def get_coupon_history(self) -> tuple:
        """쿠폰 이력 조회"""
        try:
            discount_types = self.config["DISCOUNT_TYPES"]
            discount_info = {name: {'car': 0, 'total': 0} for name in discount_types.values()}
            
            # productList 테이블 로드 대기
            await self.page.wait_for_selector('#productList tr', timeout=PLAYWRIGHT_CONFIG["TIMEOUT"])
            
            # 쿠폰 없음 체크
            empty_message = await self.page.locator('#productList td.empty').count()
            if empty_message > 0:
                logger.info("[쿠폰상태] 보유한 쿠폰이 없습니다")
                return discount_info, {name: 0 for name in discount_types.values()}, {name: 0 for name in discount_types.values()}
            
            # 쿠폰이 있는 경우 파싱
            rows = await self.page.locator('#productList tr').all()
            for row in rows:
                try:
                    cells = await row.locator('td').all()
                    if len(cells) >= 2:
                        name = (await cells[0].inner_text()).strip()
                        count_text = (await cells[1].inner_text()).strip()
                        
                        for discount_name in discount_types.values():
                            if discount_name in name:
                                car_count, total_count = 0, 0
                                if '/' in count_text:
                                    parts = count_text.split('/')
                                    car_part = parts[0].strip()
                                    total_part = parts[1].strip()
                                    car_match = re.search(r'(\d+)', car_part)
                                    total_match = re.search(r'(\d+)', total_part)
                                    car_count = int(car_match.group(1)) if car_match else 0
                                    total_count = int(total_match.group(1)) if total_match else 0
                                else:
                                    match = re.search(r'(\d+)', count_text)
                                    car_count = int(match.group(1)) if match else 0
                                    total_count = car_count
                                discount_info[discount_name] = {'car': car_count, 'total': total_count}
                                break
                except Exception as e:
                    logger.error(f"[파싱오류] 행 처리 중 오류: {str(e)}")
                    continue
            
            # 현재 보유 쿠폰 로깅
            logger.info(">>>>>[현재 적용 가능한 쿠폰]")
            for name, counts in discount_info.items():
                logger.info(f"{name}: {counts['car']}개")
            
            # 우리 매장 쿠폰 내역 (#myDcList)
            my_history = {name: 0 for name in discount_types.values()}
            try:
                my_dc_rows = await self.page.locator('#myDcList tr').all()
                for row in my_dc_rows:
                    cells = await row.locator('td').all()
                    if len(cells) >= 2:
                        name = (await cells[0].inner_text()).strip()
                        count_text = (await cells[1].inner_text()).strip()
                        
                        for discount_name in discount_types.values():
                            if discount_name in name:
                                m = re.search(r'(\d+)', count_text)
                                count = int(m.group(1)) if m else 0
                                my_history[discount_name] = count
                                break
            except Exception as e:
                logger.error(f"[myDcList] 처리 실패: {str(e)}")
            
            # 우리 매장 쿠폰 내역 로깅
            logger.info(">>>>>[우리 매장에서 적용한 쿠폰]")
            for name, count in my_history.items():
                logger.info(f"{name}: {count}개")
            
            # 전체 쿠폰 이력 (#allDcList)
            total_history = {name: 0 for name in discount_types.values()}
            try:
                total_rows = await self.page.locator('#allDcList tr').all()
                for row in total_rows:
                    cells = await row.locator('td').all()
                    if len(cells) >= 2:
                        name = (await cells[0].inner_text()).strip()
                        count_text = (await cells[1].inner_text()).strip()
                        
                        for discount_name in discount_types.values():
                            if discount_name in name:
                                m = re.search(r'(\d+)', count_text)
                                count = int(m.group(1)) if m else 0
                                total_history[discount_name] = count
                                break
            except Exception as e:
                logger.error(f"[allDcList] 처리 실패: {str(e)}")
            
            # 전체 쿠폰 이력 로깅
            logger.info(">>>>>[전체 적용된 쿠폰] (다른매장+우리매장)")
            for name, count in total_history.items():
                logger.info(f"{name}: {count}개")
            
            return discount_info, my_history, total_history
            
        except Exception as e:
            error_msg = f"쿠폰 이력 조회 실패: {str(e)}"
            logger.error(f"[쿠폰조회] {error_msg}")
            return (
                {name: {'car': 0, 'total': 0} for name in discount_types.values()},
                {name: 0 for name in discount_types.values()},
                {name: 0 for name in discount_types.values()}
            )
            
    async def apply_coupons(self, coupons_to_apply: dict) -> bool:
        """쿠폰 적용"""
        try:
            for coupon_name, count in coupons_to_apply.items():
                if count > 0:
                    # 해당 쿠폰의 행 찾기
                    rows = await self.page.locator("#productList tr").all()
                    for row in rows:
                        text = await row.inner_text()
                        if coupon_name in text:
                            # 적용 버튼 찾아서 클릭
                            apply_button = row.locator('button:has-text("적용")')
                            if await apply_button.count() > 0:
                                for _ in range(count):
                                    # 1. 쿠폰 적용 버튼 클릭
                                    await apply_button.click()
                                    logger.info(f"[쿠폰적용] {coupon_name} 적용 버튼 클릭")
                                    
                                    # 2. 첫 번째 확인 팝업 처리
                                    try:
                                        await self.page.wait_for_selector('#popupOk', timeout=PLAYWRIGHT_CONFIG["TIMEOUT"])
                                        await self.page.click('#popupOk')
                                        logger.info("[쿠폰적용] 첫 번째 확인 팝업 처리 성공")
                                        await self.page.wait_for_timeout(500)
                                    except Exception as e:
                                        logger.error(f"[쿠폰적용] 첫 번째 확인 팝업 처리 실패: {str(e)}")
                                    
                                    # 3. 두 번째 확인 팝업 처리
                                    try:
                                        await self.page.wait_for_selector('#popupOk', timeout=PLAYWRIGHT_CONFIG["TIMEOUT"])
                                        await self.page.click('#popupOk')
                                        logger.info("[쿠폰적용] 두 번째 확인 팝업 처리 성공")
                                        await self.page.wait_for_timeout(500)
                                    except Exception as e:
                                        logger.error(f"[쿠폰적용] 두 번째 확인 팝업 처리 실패: {str(e)}")
                                
                                logger.info(f"[쿠폰적용] {coupon_name} {count}개 적용 성공")
                            else:
                                logger.error(f"[쿠폰적용] {coupon_name} 적용 버튼을 찾을 수 없음")
                            break
            return True
            
        except Exception as e:
            error_msg = f"쿠폰 적용 실패: {str(e)}"
            logger.error(f"[쿠폰적용] {error_msg}")
            return False 