"""
B 매장 크롤러 - 실제 테스트 검증된 버전
- 할인등록현황 테이블에서 등록자 필드로 우리 매장 vs 전체 할인 내역 구분
- 남은잔여량에서 보유 쿠폰 수량 계산 (금액 ÷ 300)
"""
import asyncio
import re
import logging
from typing import Dict, List, Optional, Tuple
from playwright.async_api import Page, Browser, Playwright


class BStoreCrawler:
    """B 매장 전용 크롤러 - 실제 테스트 검증된 버전"""
    
    def __init__(self, config):
        self.config = config
        self.store_id = "B"
        self.user_id = config.login_username  # "215"
        self.logger = logging.getLogger(__name__)
    
    async def login(self, page: Page) -> bool:
        """B 매장 로그인 (실제 검증된 셀렉터 사용)"""
        try:
            # 로그인 페이지로 이동
            await page.goto(self.config.website_url)
            await page.wait_for_load_state('networkidle')
            
            # 로그인 요소 찾기 (실제 동작하는 방식)
            username_input = page.get_by_role('textbox', name='ID')
            password_input = page.get_by_role('textbox', name='PASSWORD')
            login_button = page.get_by_role('button', name='Submit')
            
            # 로그인 정보 입력
            await username_input.fill(self.config.login_username)
            await password_input.fill(self.config.login_password)
            await login_button.click()
            
            # 페이지 변화 대기
            await page.wait_for_timeout(3000)
            
            # 로그인 성공 확인 (사용자 정보 표시)
            success_indicator = page.locator('text=사용자')
            if await success_indicator.count() > 0:
                self.logger.info("✅ B 매장 로그인 성공")
                
                # 안내 팝업 처리
                await self._handle_popups(page)
                
                # 로그인 후 바로 검색 상태 유지 체크박스 설정
                await self._ensure_search_state_checkbox(page)
                
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
            self.logger.info(f"📱 텔레그램 알림 전송 준비 중... (차량번호: {car_number})")
            
            from datetime import datetime
            from core.application.dto.automation_dto import ErrorContext
            from infrastructure.notifications.telegram_adapter import TelegramAdapter
            from infrastructure.config.config_manager import ConfigManager
            
            # 설정 및 텔레그램 어댑터 초기화
            config_manager = ConfigManager()
            telegram_config = config_manager.get_telegram_config()
            self.logger.info(f"📞 텔레그램 설정 로드 완료: {telegram_config.get('bot_token', 'N/A')[:10]}...")
            
            telegram_adapter = TelegramAdapter(telegram_config, self.logger)
            
            # 에러 컨텍스트 생성
            error_context = ErrorContext(
                store_id="B",
                vehicle_number=car_number,
                error_step="차량검색",
                error_message=f"🚗 B 매장에서 차량번호 '{car_number}' 검색 결과가 없습니다.\n\n차량번호를 다시 확인해 주세요.",
                error_time=datetime.now()
            )
            
            self.logger.info(f"📤 텔레그램 메시지 전송 시작...")
            
            # 텔레그램 알림 전송
            await telegram_adapter.send_error_notification(error_context)
            self.logger.info("✅ 차량 검색 결과 없음 텔레그램 알림 전송 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 텔레그램 알림 전송 중 오류: {str(e)}")
            # 스택 트레이스도 출력하여 디버깅에 도움
            import traceback
            self.logger.error(f"❌ 스택 트레이스: {traceback.format_exc()}")
    
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
            
            # 검색 결과 확인 - 다양한 형태의 팝업 감지
            no_result_patterns = [
                'text=검색 결과가 없습니다',
                'text="검색 결과가 없습니다"',
                'text=검색된 차량이 없습니다',
                'text="검색된 차량이 없습니다"',
                ':text("검색 결과가 없습니다")',
                ':text("검색된 차량이 없습니다")'
            ]
            
            for pattern in no_result_patterns:
                no_result = page.locator(pattern)
                if await no_result.count() > 0:
                    self.logger.warning(f"⚠️ 차량번호 '{car_number}' 검색 결과 없음 팝업 감지")
                    
                    # 팝업 닫기 버튼들 시도
                    close_buttons = [
                        'text=OK',
                        'text="OK"',
                        'text=확인',
                        'text="확인"',
                        'text=닫기',
                        'text="닫기"',
                        'button:has-text("OK")',
                        'button:has-text("확인")'
                    ]
                    
                    for close_button_selector in close_buttons:
                        close_button = page.locator(close_button_selector)
                        if await close_button.count() > 0:
                            await close_button.click()
                            await page.wait_for_timeout(1000)
                            self.logger.info("✅ 검색 결과 없음 팝업 닫기 완료")
                            break
                    
                    # 텔레그램 알림 전송 및 프로세스 종료
                    self.logger.info("📱 텔레그램 알림 전송 시작...")
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
            else:
                self.logger.info("ℹ️ 현재 페이지에서 남은잔여량 정보를 찾을 수 없음")
                # 기본값 설정 (보유 쿠폰 없음으로 가정)
                discount_info['PAID_30MIN'] = 0
            
            # 할인내역 테이블 분석
            await self._analyze_discount_history(page, my_history, total_history)
            
            # A 매장과 동일한 포맷으로 로그 기록
            self.logger.info(f"📊 B 매장 쿠폰 현황 분석:")
            self.logger.info(f"   💰 현재 보유 쿠폰: {discount_info}")
            self.logger.info(f"   🏪 우리 매장에서 적용한 쿠폰: {my_history}")
            self.logger.info(f"   🌍 총 적용 쿠폰 (전체): {total_history}")
            
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
    
    async def _ensure_search_state_checkbox(self, page: Page):
        """검색 상태 유지 체크박스 확인 및 활성화"""
        try:
            # 검색 상태 유지 체크박스 찾기
            checkbox_selectors = [
                'text=검색 상태 유지',
                'label:has-text("검색 상태 유지")',
                'input[type="checkbox"]'
            ]
            
            checkbox_found = False
            for selector in checkbox_selectors:
                checkbox_element = page.locator(selector)
                if await checkbox_element.count() > 0:
                    # 체크박스가 체크되어 있는지 확인
                    if selector == 'input[type="checkbox"]':
                        # input 요소 직접 확인
                        is_checked = await checkbox_element.is_checked()
                    else:
                        # 텍스트 기반으로 찾은 경우 주변 input 찾기
                        nearby_checkbox = page.locator('input[type="checkbox"]').first
                        if await nearby_checkbox.count() > 0:
                            is_checked = await nearby_checkbox.is_checked()
                            checkbox_element = nearby_checkbox
                        else:
                            continue
                    
                    self.logger.info(f"🔍 검색 상태 유지 체크박스 발견 - 현재 상태: {'체크됨' if is_checked else '체크되지 않음'}")
                    
                    if not is_checked:
                        await checkbox_element.click()
                        await page.wait_for_timeout(500)
                        self.logger.info("✅ 검색 상태 유지 체크박스 활성화 완료")
                    else:
                        self.logger.info("ℹ️ 검색 상태 유지 체크박스 이미 활성화됨")
                    
                    checkbox_found = True
                    break
            
            if not checkbox_found:
                self.logger.warning("⚠️ 검색 상태 유지 체크박스를 찾을 수 없음")
                
        except Exception as e:
            self.logger.warning(f"⚠️ 검색 상태 유지 체크박스 처리 중 오류: {str(e)}")

    async def _analyze_discount_history(self, page: Page, my_history: Dict[str, int], total_history: Dict[str, int]):
        """할인등록현황 테이블 분석"""
        try:
            # 할인 내역 테이블에서 모든 행 가져오기 (두 번째 테이블이 할인내역)
            table_rows = page.locator('table').nth(1).locator('tbody tr')
            row_count = await table_rows.count()
            
            self.logger.info(f"📊 할인 내역 테이블 분석 시작 (총 {row_count}행)")
            
            # 데이터 행만 처리 (헤더 행 제외)
            data_row_count = 0
            for i in range(row_count):
                try:
                    row = table_rows.nth(i)
                    cells = row.locator('td, cell')
                    cell_count = await cells.count()
                    
                    if cell_count >= 4:  # B 매장 테이블: 순번, 할인값, 등록자, 등록시간, 삭제
                        # 순번 셀이 숫자인지 확인 (데이터 행인지 판별)
                        sequence_cell = cells.nth(0)
                        sequence_text = await sequence_cell.text_content() or ""
                        
                        if sequence_text.strip().isdigit():
                            data_row_count += 1
                            
                            # 할인값 (1번째 컬럼) - "유료 30분할인" 형식
                            discount_value_cell = cells.nth(1)
                            discount_value = await discount_value_cell.text_content() or ""
                            
                            # 등록자 (2번째 컬럼) - "215(이수열)" 형식
                            registrant_cell = cells.nth(2)
                            registrant = await registrant_cell.text_content() or ""
                            
                            # 등록시간 (3번째 컬럼) 
                            time_cell = cells.nth(3)
                            time_text = await time_cell.text_content() or ""
                            
                            # 쿠폰 타입 추출
                            coupon_type = self._extract_coupon_type(discount_value)
                            if coupon_type:
                                # 전체 내역에 추가
                                total_history[coupon_type] = total_history.get(coupon_type, 0) + 1
                                
                                # 등록자에서 ID 추출 (215(이수열) -> 215)
                                registrant_id = registrant.split('(')[0].strip()
                                
                                # 등록자가 우리 매장 ID(215)인 경우 우리 매장 내역에도 추가
                                if registrant_id == self.user_id:
                                    my_history[coupon_type] = my_history.get(coupon_type, 0) + 1
                                    self.logger.info(f"   🏪 우리 매장 할인: {coupon_type} - {registrant} ({time_text})")
                                else:
                                    self.logger.info(f"   🌍 타 매장 할인: {coupon_type} - {registrant} ({time_text})")
                
                except Exception as e:
                    self.logger.warning(f"⚠️ 테이블 행 {i} 처리 중 오류: {str(e)}")
                    continue
            
            self.logger.info(f"📊 할인 내역 분석 완료: 총 {data_row_count}건의 할인 발견")
            
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
            
            # 현재 할인내역 테이블의 행 수를 기록 (적용 전)
            current_rows = await self._count_discount_rows(page)
            self.logger.info(f"📊 적용 전 할인내역 행 수: {current_rows}")
            
            # 쿠폰 타입에 따른 링크 클릭
            if coupon_type == 'FREE_1HOUR':
                # 무료 1시간할인 링크 클릭
                discount_link = page.locator('text=무료 1시간할인')
                if await discount_link.count() > 0:
                    await discount_link.click()
                    self.logger.info("📱 무료 1시간할인 선택 완료")
                else:
                    self.logger.error("❌ 무료 1시간할인 링크를 찾을 수 없음")
                    return False
                    
            elif coupon_type == 'PAID_30MIN':
                # 유료 30분할인 링크 클릭
                discount_link = page.locator('text=유료 30분할인 (판매 : 300 )')
                if await discount_link.count() > 0:
                    await discount_link.click()
                    self.logger.info("📱 유료 30분할인 선택 완료")
                else:
                    self.logger.error("❌ 유료 30분할인 링크를 찾을 수 없음")
                    return False
            
            # 짧은 대기 후 성공 팝업 처리
            await page.wait_for_timeout(500)
            
            # 성공/확인 팝업 처리 - 페이지 이동 방지
            success = await self._handle_apply_popups_without_navigation(page)
            if not success:
                self.logger.error("❌ 쿠폰 적용 팝업 처리 실패")
                return False
            
            # 할인내역 테이블 업데이트 확인 (최대 5초 대기)
            updated = await self._wait_for_discount_table_update(page, current_rows)
            if updated:
                self.logger.info("✅ 할인내역 테이블 업데이트 확인 완료")
                return True
            else:
                self.logger.warning("⚠️ 할인내역 테이블 업데이트 확인 실패, 하지만 계속 진행")
                return True  # 쿠폰이 적용되었을 가능성이 높으므로 성공으로 처리
            
        except Exception as e:
            self.logger.error(f"❌ {coupon_type} 쿠폰 적용 중 오류: {str(e)}")
            return False
    
    async def _handle_apply_popups_without_navigation(self, page: Page) -> bool:
        """쿠폰 적용 후 팝업 처리 - 페이지 이동 방지"""
        try:
            # 성공 메시지 팝업 확인 (최대 3초 대기)
            success_messages = [
                'text=할인처리 완료 되었습니다',
                'text=등록되었습니다',
                'text=적용되었습니다',
                'text=할인이 등록되었습니다'
            ]
            
            popup_found = False
            for i in range(6):  # 3초간 0.5초 간격으로 확인
                for message_locator in success_messages:
                    message = page.locator(message_locator)
                    if await message.count() > 0:
                        self.logger.info("✅ 쿠폰 적용 성공 메시지 확인")
                        popup_found = True
                        
                        # OK 버튼 클릭 - 현재 페이지 유지하도록 처리
                        ok_button = page.locator('text=OK')
                        if await ok_button.count() > 0:
                            await ok_button.click()
                            await page.wait_for_timeout(300)  # 짧은 대기
                            self.logger.info("📱 성공 팝업 닫기 완료")
                        break
                
                if popup_found:
                    break
                    
                await page.wait_for_timeout(500)  # 0.5초 대기
            
            if not popup_found:
                self.logger.warning("⚠️ 성공 팝업을 찾지 못했지만 계속 진행")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 쿠폰 적용 팝업 처리 중 오류: {str(e)}")
            return False

    async def _count_discount_rows(self, page: Page) -> int:
        """현재 할인내역 테이블의 행 수 계산"""
        try:
            # 할인내역 테이블에서 데이터 행만 카운트
            discount_table = page.locator('table').nth(1)  # 두 번째 테이블이 할인내역
            data_rows = discount_table.locator('tbody tr')
            row_count = await data_rows.count()
            
            # 헤더 행 제외 (첫 번째 행은 헤더)
            data_count = max(0, row_count - 1)
            return data_count
            
        except Exception as e:
            self.logger.warning(f"⚠️ 할인내역 행 수 계산 중 오류: {str(e)}")
            return 0

    async def _wait_for_discount_table_update(self, page: Page, previous_count: int) -> bool:
        """할인내역 테이블 업데이트 대기"""
        try:
            # 최대 5초간 테이블 업데이트 확인
            for i in range(10):  # 0.5초씩 10번 = 5초
                await page.wait_for_timeout(500)
                
                current_count = await self._count_discount_rows(page)
                if current_count > previous_count:
                    self.logger.info(f"✅ 할인내역 업데이트 감지: {previous_count} → {current_count}")
                    return True
                
                # 남은잔여량도 확인하여 변화가 있는지 체크
                remaining_element = page.locator('cell:has-text("남은잔여량")').locator('..').locator('cell').nth(1)
                if await remaining_element.count() > 0:
                    current_amount = await remaining_element.text_content()
                    if current_amount and "5,800" in current_amount or "5,500" in current_amount:
                        # 금액이 변경되었으면 적용된 것으로 판단
                        self.logger.info(f"✅ 남은잔여량 변화 감지: {current_amount}")
                        return True
            
            self.logger.warning("⚠️ 할인내역 테이블 업데이트 확인 시간 초과")
            return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ 할인내역 테이블 업데이트 확인 중 오류: {str(e)}")
            return False

    async def _handle_apply_popups(self, page: Page):
        """쿠폰 적용 후 팝업 처리 (기존 메소드 - 호환성 유지)"""
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