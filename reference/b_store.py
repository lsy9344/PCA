"""
B 매장 구현체
"""
from datetime import datetime
from playwright.async_api import TimeoutError
from ..stores.base_store import BaseStore
from config.global_config import STORE_CONFIGS, PLAYWRIGHT_CONFIG, TELEGRAM_CONFIG
from utils.telegram_notifier import TelegramNotifier
from utils.logger import setup_logger
from discount_rules.b_discount import BDiscountRule
import re
from typing import Dict

logger = setup_logger(__name__)

class BStore(BaseStore):
    """B 매장 구현체"""
    
    def __init__(self):
        super().__init__()
        self.config = STORE_CONFIGS["B"]
        self.telegram = TelegramNotifier(
            TELEGRAM_CONFIG["BOT_TOKEN"],
            TELEGRAM_CONFIG["CHAT_ID"]
        )
        self.discount_rule = BDiscountRule()  # B 매장 전용 쿠폰 규칙 사용
        
    async def login(self) -> bool:
        """로그인 수행 (팝업 처리 포함)"""
        try:
            # 웹사이트 접속
            await self.page.goto(self.config["WEBSITE_URL"])
            logger.info("[시작] B 매장 자동화 시작")
            
            # 로그인 폼 입력
            await self.page.fill('#userId', self.config["LOGIN"]["USERNAME"])
            await self.page.fill('#userPwd', self.config["LOGIN"]["PASSWORD"])
            await self.page.click('input[type="submit"]')
            logger.info("[로그인] 로그인 정보 입력 후 로그인 버튼 클릭")            
            
            # 로그인 성공 후 안내 팝업 처리 (있으면 처리, 없으면 건너뜀)
            try:
                # 안내 메시지 팝업 확인 (로그인 성공 확인)
                notice_popup = self.page.locator('div').filter(has_text='안내')
                if await notice_popup.count() > 0:
                    await notice_popup.first.click()
                    logger.info('[로그인] 안내 메시지 팝업 확인 (로그인 성공)')
                    
                    # OK 버튼 클릭
                    await self.page.get_by_text('OK').click()
                    logger.info("[로그인 후] OK 버튼 클릭 성공")
                else:
                    logger.info('[로그인] 안내 팝업이 없음 - 바로 다음 단계 진행')
            except Exception as e:
                logger.warning(f"[로그인 후] 안내 팝업 처리 중 오류 (무시하고 진행): {str(e)}")
                # 팝업 처리 실패해도 로그인은 성공으로 간주하고 계속 진행
            return True
            
        except TimeoutError:
            error_msg = "로그인 실패: 로그인 성공 후 뜨는 팝업창이이 나타나지 않음"
            logger.error(f"[로그인] {error_msg}")
            await self.telegram.send_error(error_msg, "B", None)
            return False
        except Exception as e:
            error_msg = f"로그인 실패: {str(e)}"
            logger.error(f"[로그인] {error_msg}")
            await self.telegram.send_error(error_msg, "B", None)
            return False
            
    async def search_car(self, car_number: str) -> bool:
        """차량 검색"""
        try:
            # 차량번호 입력
            await self.page.fill('input[name="carNo"]', car_number)
            logger.info('[차량검색] 차량 번호 입력 성공')
            
            # 검색 버튼 클릭
            await self.page.get_by_role('button', name='검색').click()
            logger.info('[차량검색] 검색 버튼 클릭 성공')
            
            # 검색 결과 대기
            await self.page.wait_for_timeout(1000)  # 결과 로딩 대기
            
            # 검색 결과 없음 확인
            try:
                modal = await self.page.wait_for_selector('div.modal-text', timeout=3000)
                modal_text = await modal.inner_text()
                if modal_text.strip().startswith('검색 결과가 없습니다'):
                    error_msg = "검색된 차량이 없습니다"
                    logger.error(f"[차량검색] {error_msg}")
                    await self.telegram.send_error(error_msg, "B", car_number)
                    return False
            except:
                pass  # 모달이 없으면 정상 진행
                
            # 차량번호 확인
            try:
                await self.page.click(f'text={car_number}')
                logger.info(f'[차량검색] 차량번호 {car_number} 확인 성공')
            except Exception as e:
                error_msg = f'[차량검색] 차량번호 확인 실패: {str(e)}'
                logger.error(error_msg)
                await self.telegram.send_error(error_msg, "B", car_number)
                return False
            
            logger.info(f"[차량검색] 차량번호 {car_number} 검색 및 선택 성공")
            return True
            
        except Exception as e:
            error_msg = f"차량 검색 실패: {str(e)}"
            logger.error(f"[차량검색] {error_msg}")
            await self.telegram.send_error(error_msg, "B", car_number)
            return False
            
    async def get_coupon_history(self) -> tuple:
        """쿠폰 이력 조회"""
        try:
            discount_types = self.config["DISCOUNT_TYPES"]
            discount_info = {name: {'car': 0, 'total': 0} for name in discount_types.values()}
            
            # 현재 보유 쿠폰 수량 계산 (가격 / 300)
            try:
                # 가격 정보가 있는 label 요소 찾기 (HTML 구조 기반)
                price_labels = await self.page.locator('label.un.t-R').all()
                
                for label in price_labels:
                    text = await label.inner_text()
                    text = text.strip()
                    
                    # 가격 패턴 매칭 (15,400 형태 - 쉼표 포함)
                    price_match = re.search(r'^(\d{1,3}(?:,\d{3})*)$', text)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        try:
                            price = int(price_str)
                            # 유의미한 가격인지 확인 (1000원 이상)
                            if price >= 1000:
                                # 가격을 300으로 나누어 쿠폰 수량 계산
                                coupon_count = price // 300
                                logger.info(f"[쿠폰조회] 발견된 가격: {price}원, 계산된 쿠폰 수량: {coupon_count}개")
                                
                                # 유료 30분할인 쿠폰으로 설정 (가격이 있는 쿠폰)
                                if "유료 30분할인" in discount_types.values():
                                    discount_info["유료 30분할인"] = {'car': coupon_count, 'total': coupon_count}
                                break
                        except ValueError:
                            continue
                
                # 위 방법으로 찾지 못한 경우 대안 방법
                if "유료 30분할인" in discount_types.values() and discount_info["유료 30분할인"]['car'] == 0:
                    # 모든 텍스트에서 큰 금액 찾기
                    all_text = await self.page.inner_text('body')
                    price_matches = re.findall(r'(\d{1,3}(?:,\d{3})+)', all_text)
                    
                    for price_str in price_matches:
                        try:
                            price = int(price_str.replace(',', ''))
                            if price >= 5000:  # 5,000원 이상인 경우만
                                coupon_count = price // 300
                                logger.info(f"[쿠폰조회] 대안방법으로 발견된 가격: {price}원, 계산된 쿠폰 수량: {coupon_count}개")
                                discount_info["유료 30분할인"] = {'car': coupon_count, 'total': coupon_count}
                                break
                        except ValueError:
                            continue
                
                # 무료 1시간할인은 무제한으로 설정
                if "무료 1시간할인" in discount_types.values():
                    discount_info["무료 1시간할인"] = {'car': 999, 'total': 999}
                    
            except Exception as e:
                logger.error(f"[쿠폰조회] 보유 쿠폰 수량 계산 실패: {str(e)}")
                # 실패시 기본값 설정
                for name in discount_types.values():
                    discount_info[name] = {'car': 999, 'total': 999}
            
            # 할인내역 테이블에서 이미 적용된 쿠폰 수 파악
            # 모든 가능한 쿠폰 타입 초기화 (다른 매장에서 적용한 쿠폰 포함)
            all_coupon_types = ["무료 1시간할인", "유료 30분할인", "유료 1시간할인"]
            my_history = {coupon_type: 0 for coupon_type in all_coupon_types}
            
            try:
                # '할인내역' 테이블 찾기
                await self.page.click('text=할인내역')
                logger.info("[쿠폰조회] 할인내역 테이블 접근")
                
                # 할인내역 테이블에서 각 쿠폰 타입별 개수 확인
                for coupon_type in all_coupon_types:
                    try:
                        # li 태그 안의 텍스트로 쿠폰 개수 확인 (HTML 구조 기반)
                        coupon_cells = await self.page.locator(f'li:has-text("{coupon_type}")').count()
                        my_history[coupon_type] = coupon_cells
                        logger.info(f"[쿠폰조회] {coupon_type}: {coupon_cells}개 적용됨")
                        
                        # 대안 방법: td 안의 li 태그도 확인
                        if coupon_cells == 0:
                            coupon_cells_alt = await self.page.locator(f'td li:has-text("{coupon_type}")').count()
                            my_history[coupon_type] = coupon_cells_alt
                            logger.info(f"[쿠폰조회] {coupon_type} (대안방법): {coupon_cells_alt}개 적용됨")
                            
                    except Exception as e:
                        logger.warning(f"[쿠폰조회] {coupon_type} 개수 확인 실패: {str(e)}")
                        my_history[coupon_type] = 0
                
            except Exception as e:
                logger.error(f"[쿠폰조회] 할인내역 테이블 파싱 실패: {str(e)}")
            
            # 현재 보유 쿠폰 로깅
            logger.info(">>>>>[현재 적용 가능한 쿠폰]")
            for name, counts in discount_info.items():
                logger.info(f"{name}: {counts['car']}개")
            
            # 우리 매장 쿠폰 내역 로깅 (실제 적용 가능한 쿠폰만)
            logger.info(">>>>>[우리 매장에서 적용한 쿠폰]")
            our_store_history = {name: my_history.get(name, 0) for name in discount_types.values()}
            for name, count in our_store_history.items():
                logger.info(f"{name}: {count}개")
            
            # 전체 쿠폰 내역 로깅 (다른 매장 포함)
            logger.info(">>>>>[전체 적용된 쿠폰 (모든 매장)]")
            for coupon_type, count in my_history.items():
                if count > 0:
                    logger.info(f"{coupon_type}: {count}개")
            
            # B 매장은 total_history를 my_history와 동일하게 반환
            total_history = my_history.copy()
            
            return discount_info, our_store_history, total_history
            
        except Exception as e:
            error_msg = f"쿠폰 이력 조회 실패: {str(e)}"
            logger.error(f"[쿠폰조회] {error_msg}")
            await self.telegram.send_error(error_msg, "B", None)
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
                    for _ in range(count):
                        # 쿠폰 적용 버튼 클릭
                        if coupon_name == "무료 1시간할인":
                            await self.page.click('a:has-text("무료 1시간할인")')
                        elif coupon_name == "유료 30분할인":
                            await self.page.click('a:has-text("유료 30분할인")')
                        logger.info(f"[쿠폰적용] {coupon_name} 적용 버튼 클릭")
                        
                        # 등록 확인 팝업 처리
                        await self.page.click('text=등록되었습니다')
                        await self.page.click('text=OK')
                        logger.info(f"[쿠폰적용] {coupon_name} 등록 확인")
                        
                        # 할인내역 테이블에서 쿠폰 적용 확인
                        await self.page.click(f'text={coupon_name}')
                        logger.info(f"[쿠폰적용] {coupon_name} 적용 확인")
                        
                        # 다음 쿠폰 적용 전 대기
                        await self.page.wait_for_timeout(1000)
                    
                    logger.info(f"[쿠폰적용] {coupon_name} {count}개 적용 성공")
            
            return True
            
        except Exception as e:
            error_msg = f"쿠폰 적용 실패: {str(e)}"
            logger.error(f"[쿠폰적용] {error_msg}")
            await self.telegram.send_error(error_msg, "B", None)
            return False 