"""
A 매장 쿠폰 적용 테스트
AWS CloudWatch Logs 비용 최적화 적용
"""
import asyncio
import logging
import os
from datetime import datetime
from playwright.async_api import async_playwright

from infrastructure.web_automation.store_crawlers.a_store_crawler import AStoreCrawler
from infrastructure.config.config_manager import ConfigManager
from infrastructure.logging.structured_logger import StructuredLogger
from infrastructure.notifications.telegram_adapter import TelegramAdapter
from core.domain.models.vehicle import Vehicle
from core.domain.models.coupon import CouponApplication, CouponType
from core.application.dto.automation_dto import ErrorContext
from utils.optimized_logger import get_optimized_logger

# 최적화된 로거 사용
logger = get_optimized_logger(__name__)

class AStoreCouponTester:
    """A 매장 쿠폰 적용 테스터 (로깅 최적화 버전)"""
    
    def __init__(self):
        self.crawler = None
        self.config_manager = ConfigManager()
        self.telegram_adapter = None
        self.playwright = None
        self.browser = None
        
    async def setup(self):
        """테스트 환경 설정"""
        try:
            # Playwright 초기화
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            
            # 설정 로드
            store_config = self.config_manager.get_store_config("A")
            playwright_config = self.config_manager.get_playwright_config()
            
            # 구조화된 로거 초기화
            log_config = {
                'level': 'INFO',
                'log_dir': './logs',
                'max_file_size': 10 * 1024 * 1024,  # 10MB
                'backup_count': 5
            }
            structured_logger = StructuredLogger("test_a_store", log_config)
            
            # A 매장 크롤러 초기화
            self.crawler = AStoreCrawler(store_config, playwright_config, structured_logger)
            await self.crawler._initialize_browser()
            
            # 텔레그램 어댑터 초기화
            telegram_config = {
                'bot_token': "7694000458:AAFDa7szcGRjJJUy8cU_eJnU9MPgqsWnkmk",
                'chat_id': "6968094848",
                'max_retries': 3,
                'retry_delay': 1.0
            }
            self.telegram_adapter = TelegramAdapter(telegram_config, structured_logger)
            
            # 개발 환경에서만 설정 완료 로그 기록
            if logger.should_log_info():
                logger.log_info("[테스트 설정] A 매장 크롤러 및 텔레그램 어댑터 초기화 완료")
            
        except Exception as e:
            logger.log_error("A", "테스트설정", "FAIL_SETUP", str(e))
            raise
    
    async def test_login(self):
        """로그인 테스트"""
        try:
            # 개발 환경에서만 시작 로그 기록
            if logger.should_log_info():
                logger.log_info("[테스트] 로그인 테스트 시작")
            
            result = await self.crawler.login()
            if result:
                if logger.should_log_info():
                    logger.log_info("[테스트] ✅ 로그인 성공")
                return True
            else:
                logger.log_error("A", "로그인", "FAIL_AUTH", "로그인 실패")
                await self.send_error_notification("로그인", "로그인 실패")
                return False
                
        except Exception as e:
            logger.log_error("A", "로그인", "FAIL_AUTH", str(e))
            await self.send_error_notification("로그인", str(e))
            return False
    
    async def test_vehicle_search(self, car_number: str):
        """차량 검색 테스트 (reference/a_store.py 로직 적용)"""
        try:
            # 개발 환경에서만 시작 로그 기록
            if logger.should_log_info():
                logger.log_info(f"[테스트] 차량 검색 테스트 시작: {car_number}")
            
            # 차량번호 입력
            await self.crawler.page.fill("#carNumber", car_number)
            if logger.should_log_info():
                self.crawler.logger.log_info('[차량검색] 차량 번호 입력 성공')
            
            # 검색 버튼 클릭 (여러 셀렉터 시도)
            try:
                await self.crawler.page.click('button[name="search"]')
            except:
                try:
                    await self.crawler.page.click('.btn-search')
                except:
                    await self.crawler.page.click('button:has-text("검색")')
            
            # 검색 결과 대기
            await self.crawler.page.wait_for_timeout(1000)
            
            # [추가] #parkName의 텍스트가 '검색된 차량이 없습니다.'인지 확인
            try:
                park_name_elem = self.crawler.page.locator('#parkName')
                if await park_name_elem.count() > 0:
                    park_name_text = await park_name_elem.inner_text()
                    if '검색된 차량이 없습니다.' in park_name_text:
                        logger.log_error("A", "차량검색", "NO_VEHICLE", f"차량번호 {car_number} 검색 결과 없음")
                        await self.send_error_notification("차량검색", f"차량번호 {car_number} 검색 결과 없음", car_number)
                        return False, None
            except Exception:
                pass
            
            # 기존: 검색 결과 확인
            no_result = self.crawler.page.locator('text="검색된 차량이 없습니다"')
            if await no_result.count() > 0:
                logger.log_error("A", "차량검색", "NO_VEHICLE", f"차량번호 {car_number} 검색 결과 없음")
                await self.send_error_notification("차량검색", f"차량번호 {car_number} 검색 결과 없음", car_number)
                return False, None
                
            # 차량 선택 버튼 클릭
            try:
                await self.crawler.page.click('#next')
                if logger.should_log_info():
                    logger.log_info('[차량검색] 차량 선택 버튼 클릭 성공')
                await self.crawler.page.wait_for_timeout(5000)
            except Exception as e1:
                try:
                    await self.crawler.page.click('button:has-text("차량 선택")')
                    if logger.should_log_info():
                        logger.log_info('[차량검색] button:has-text("차량 선택") 버튼 클릭 성공')
                    await self.crawler.page.wait_for_timeout(3000)
                except Exception as e2:
                    error_msg = f'차량 선택 버튼 클릭 실패: #next: {str(e1)}, has-text: {str(e2)}'
                    logger.log_error("A", "차량검색", "FAIL_SEARCH", error_msg)
                    await self.send_error_notification("차량검색", error_msg, car_number)
                    return False, None
            
            if logger.should_log_info():
                logger.log_info(f"[차량검색] 차량번호 {car_number} 검색 및 선택 후 페이지 로딩 성공")
            return True, car_number
            
        except Exception as e:
            logger.log_error("A", "차량검색", "FAIL_SEARCH", str(e))
            await self.send_error_notification("차량검색", str(e), car_number)
            return False, None
    
    async def test_coupon_history(self, car_number: str):
        """쿠폰 이력 조회 테스트"""
        try:
            # 개발 환경에서만 시작 로그 기록
            if logger.should_log_info():
                logger.log_info("[테스트] 쿠폰 이력 조회 테스트 시작")
            
            # reference/a_store.py의 get_coupon_history 로직 적용
            store_config = self.config_manager.get_store_config("A")
            discount_types = store_config.discount_types
            discount_info = {name: {'car': 0, 'total': 0} for name in discount_types.values()}
            
            # productList 테이블 로드 대기
            await self.crawler.page.wait_for_selector('#productList tr', timeout=30000)
            
            # 쿠폰 없음 체크
            empty_message = await self.crawler.page.locator('#productList td.empty').count()
            if empty_message > 0:
                if logger.should_log_info():
                    logger.log_info("[쿠폰상태] 보유한 쿠폰이 없습니다")
                return True, {
                    'available_coupons': {name: 0 for name in discount_types.values()},
                    'my_history': {name: 0 for name in discount_types.values()},
                    'total_history': {name: 0 for name in discount_types.values()}
                }
            
            # 쿠폰이 있는 경우 파싱 (로그 최소화)
            rows = await self.crawler.page.locator('#productList tr').all()
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
                                    import re
                                    car_match = re.search(r'(\d+)', car_part)
                                    total_match = re.search(r'(\d+)', total_part)
                                    car_count = int(car_match.group(1)) if car_match else 0
                                    total_count = int(total_match.group(1)) if total_match else 0
                                else:
                                    import re
                                    match = re.search(r'(\d+)', count_text)
                                    car_count = int(match.group(1)) if match else 0
                                    total_count = car_count
                                discount_info[discount_name] = {'car': car_count, 'total': total_count}
                                break
                except Exception:
                    continue  # 파싱 오류는 로그 기록하지 않고 계속 진행
            
            # 개발 환경에서만 현재 보유 쿠폰 로깅
            if logger.should_log_info():
                logger.log_info(">>>>>[현재 적용 가능한 쿠폰]")
                for name, counts in discount_info.items():
                    logger.log_info(f"{name}: {counts['car']}개")
            
            # 우리 매장 쿠폰 내역 (#myDcList) - 로그 최소화
            my_history = {name: 0 for name in discount_types.values()}
            try:
                my_dc_rows = await self.crawler.page.locator('#myDcList tr').all()
                for row in my_dc_rows:
                    cells = await row.locator('td').all()
                    if len(cells) >= 2:
                        name = (await cells[0].inner_text()).strip()
                        count_text = (await cells[1].inner_text()).strip()
                        
                        for discount_name in discount_types.values():
                            if discount_name in name:
                                import re
                                m = re.search(r'(\d+)', count_text)
                                count = int(m.group(1)) if m else 0
                                my_history[discount_name] = count
                                break
            except Exception:
                pass  # myDcList 처리 실패는 로그 기록하지 않음
            
            # 개발 환경에서만 우리 매장 쿠폰 내역 로깅
            if logger.should_log_info():
                logger.log_info(">>>>>[우리 매장에서 적용한 쿠폰]")
                for name, count in my_history.items():
                    logger.log_info(f"{name}: {count}개")
            
            # 전체 쿠폰 이력 (#allDcList) - 로그 최소화
            total_history = {name: 0 for name in discount_types.values()}
            try:
                total_rows = await self.crawler.page.locator('#allDcList tr').all()
                for row in total_rows:
                    cells = await row.locator('td').all()
                    if len(cells) >= 2:
                        name = (await cells[0].inner_text()).strip()
                        count_text = (await cells[1].inner_text()).strip()
                        
                        for discount_name in discount_types.values():
                            if discount_name in name:
                                import re
                                m = re.search(r'(\d+)', count_text)
                                count = int(m.group(1)) if m else 0
                                total_history[discount_name] = count
                                break
            except Exception:
                pass  # allDcList 처리 실패는 로그 기록하지 않음
            
            # 개발 환경에서만 전체 쿠폰 이력 로깅
            if logger.should_log_info():
                logger.log_info(">>>>>[전체 적용된 쿠폰] (다른매장+우리매장)")
                for name, count in total_history.items():
                    logger.log_info(f"{name}: {count}개")
            
            coupon_history = {
                'available_coupons': {name: counts['car'] for name, counts in discount_info.items()},
                'my_history': my_history,
                'total_history': total_history
            }
            
            if logger.should_log_info():
                logger.log_info("[테스트] ✅ 쿠폰 이력 조회 성공")
            return True, coupon_history
            
        except Exception as e:
            logger.log_error("A", "쿠폰조회", "FAIL_PARSE", str(e))
            await self.send_error_notification("쿠폰조회", str(e), car_number)
            return False, None
    
    async def test_coupon_application(self, test_applications: list, available_coupons: dict):
        """쿠폰 적용 테스트"""
        try:
            # 개발 환경에서만 시작 로그 기록
            if logger.should_log_info():
                logger.log_info("[테스트] 쿠폰 적용 테스트 시작")
            
            # 적용 가능 여부 미리 확인
            for app_data in test_applications:
                coupon_name = app_data['name']
                required_count = app_data['count']
                available_count = available_coupons.get(coupon_name, 0)
                
                if required_count > available_count:
                    error_msg = f"{coupon_name} 적용 실패: 필요 {required_count}개, 보유 {available_count}개"
                    logger.log_error("A", "쿠폰적용", "FAIL_APPLY", error_msg)
                    await self.send_error_notification("쿠폰적용", error_msg)
                    return False
                
                # 개발 환경에서만 적용 예정 로그 기록
                if logger.should_log_info():
                    logger.log_info(f"[테스트] 적용 예정: {coupon_name} {required_count}개 (보유: {available_count}개)")
            
            # CouponApplication 객체 생성
            applications = []
            for app_data in test_applications:
                # 쿠폰 타입 결정
                coupon_type = CouponType.FREE
                if "유료" in app_data['name']:
                    if "주말" in app_data['name']:
                        coupon_type = CouponType.WEEKEND
                    else:
                        coupon_type = CouponType.PAID
                
                app = CouponApplication(
                    coupon_name=app_data['name'],
                    coupon_type=coupon_type,
                    count=app_data['count']
                )
                applications.append(app)
            
            # 실제 쿠폰 적용
            result = await self.crawler.apply_coupons(applications)
            
            if result:
                if logger.should_log_info():
                    logger.log_info("[테스트] ✅ 쿠폰 적용 성공")
                return True
            else:
                logger.log_error("A", "쿠폰적용", "FAIL_APPLY", "apply_coupons 메서드가 False 반환")
                return False
                
        except Exception as e:
            error_msg = f"쿠폰 적용 중 예외 발생: {str(e)}"
            logger.log_error("A", "쿠폰적용", "FAIL_APPLY", error_msg)
            await self.send_error_notification("쿠폰적용", error_msg)
            return False
    
    async def send_error_notification(self, error_step: str, error_message: str, vehicle_number: str = None):
        """오류 발생 시 텔레그램 알림 전송"""
        if self.telegram_adapter:
            try:
                error_context = ErrorContext(
                    store_id="A",
                    vehicle_number=vehicle_number,
                    error_step=error_step,
                    error_message=error_message,
                    error_time=datetime.now()
                )
                
                await self.telegram_adapter.send_error_notification(error_context)
                
                # 개발 환경에서만 알림 전송 성공 로그 기록
                if logger.should_log_info():
                    logger.log_info("[텔레그램] 오류 알림 전송 성공")
                    
            except Exception as e:
                logger.log_error("A", "텔레그램", "FAIL_NOTIFY", str(e))
    
    async def cleanup(self):
        """테스트 정리 (AsyncIO 리소스 정리 개선)"""
        import asyncio
        
        try:
            # 1. 크롤러 정리
            if self.crawler:
                try:
                    await self.crawler.cleanup()
                    if logger.should_log_info():
                        logger.log_info("[테스트 정리] 크롤러 정리 완료")
                except Exception as e:
                    logger.log_warning("A", "정리", f"크롤러 정리 실패: {str(e)}")
                finally:
                    self.crawler = None
            
            # 2. 페이지 정리
            if hasattr(self, 'page') and self.page:
                try:
                    await self.page.close()
                    if logger.should_log_info():
                        logger.log_info("[테스트 정리] 페이지 종료 완료")
                except Exception as e:
                    logger.log_warning("A", "정리", f"페이지 종료 실패: {str(e)}")
                finally:
                    self.page = None
            
            # 3. 브라우저 정리
            if self.browser:
                try:
                    await self.browser.close()
                    if logger.should_log_info():
                        logger.log_info("[테스트 정리] 브라우저 종료 완료")
                except Exception as e:
                    logger.log_warning("A", "정리", f"브라우저 종료 실패: {str(e)}")
                finally:
                    self.browser = None
            
            # 4. Playwright 정리
            if self.playwright:
                try:
                    await self.playwright.stop()
                    if logger.should_log_info():
                        logger.log_info("[테스트 정리] Playwright 종료 완료")
                except Exception as e:
                    logger.log_warning("A", "정리", f"Playwright 종료 실패: {str(e)}")
                finally:
                    self.playwright = None
            
            # 5. 리소스 정리 완료를 위한 대기
            await asyncio.sleep(1.0)
            
        except Exception as e:
            logger.log_warning("A", "정리", f"전체 정리 과정 중 오류: {str(e)}")

    def decide_coupon_to_apply(self, my_history: dict, total_history: dict, discount_types: dict, available_coupons: dict) -> dict:
        """
        적용할 쿠폰 개수 결정 (discount_logic.py 로직 적용)
        """
        # 현재 시간으로 평일/주말 판단
        from datetime import datetime
        now = datetime.now()
        is_weekday_bool = now.weekday() < 5
        
        # 쿠폰 키 매핑
        free_key = None
        paid_key = None
        weekend_key = None
        
        for key, value in discount_types.items():
            if "30분할인권(무료)" in value:
                free_key = value
            elif "1시간할인권(유료)" in value:
                paid_key = value
            elif "1시간주말할인권(유료)" in value:
                weekend_key = value
        
        if not all([free_key, paid_key, weekend_key]):
            logger.log_error("A", "쿠폰로직", "FAIL_PARSE", "쿠폰 타입을 찾을 수 없습니다")
            return {}
        
        total_free_used = total_history.get(free_key, 0)
        my_free = my_history.get(free_key, 0)
        my_paid = my_history.get(paid_key, 0)
        my_weekend = my_history.get(weekend_key, 0)
        
        # 보유 쿠폰 확인
        available_free = available_coupons.get(free_key, 0)
        available_paid = available_coupons.get(paid_key, 0)
        available_weekend = available_coupons.get(weekend_key, 0)
        
        if is_weekday_bool:
            total_needed = 3  # 평일 3시간
            already_applied = my_free + my_paid
            remaining_needed = max(0, total_needed - already_applied)
            
            free_apply = 0 if total_free_used > 0 else min(available_free, max(0, 1 - my_free))
            paid_apply = min(available_paid, max(0, remaining_needed - free_apply))
            
            result = {
                free_key: free_apply,
                paid_key: paid_apply,
                weekend_key: 0
            }
            
            # 개발 환경에서만 로직 로그 기록
            if logger.should_log_info():
                logger.log_info(f"[쿠폰 로직] 평일 모드: 총 {total_needed}시간 필요, 이미 적용: {already_applied}시간")
        else:
            total_needed = 2  # 주말 2시간
            already_applied = my_free + my_weekend
            remaining_needed = max(0, total_needed - already_applied)
            
            free_apply = 0 if total_free_used > 0 else min(available_free, max(0, 1 - my_free))
            weekend_apply = min(available_weekend, max(0, remaining_needed - free_apply))
            
            result = {
                free_key: free_apply,
                paid_key: 0,
                weekend_key: weekend_apply
            }
            
            # 개발 환경에서만 로직 로그 기록
            if logger.should_log_info():
                logger.log_info(f"[쿠폰 로직] 주말 모드: 총 {total_needed}시간 필요, 이미 적용: {already_applied}시간")
        
        # 개발 환경에서만 적용할 쿠폰 결과 로깅
        if logger.should_log_info():
            logger.log_info(">>>>>[적용할 쿠폰]<<<<<")
            for name, count in result.items():
                if count > 0:
                    logger.log_info(f"{name}: {count}개")
        
        return result

async def run_full_test():
    """전체 테스트 실행 (AsyncIO 리소스 정리 개선 버전)"""
    tester = AStoreCouponTester()
    
    try:
        print("=== A 매장 쿠폰 적용 테스트 ===")
        print("AWS CloudWatch Logs 비용 최적화 버전")
        print("참고 코드 기반의 검증된 로직으로 테스트를 수행합니다.")
        
        # 1. 테스트 환경 설정
        await tester.setup()
        
        # 2. 로그인 테스트
        login_success = await tester.test_login()
        if not login_success:
            print("❌ 로그인 실패로 테스트 중단")
            return
        
        # 3. 차량 검색 테스트
        car_number = input("테스트할 차량번호를 입력하세요: ")
        search_success, vehicle_number = await tester.test_vehicle_search(car_number)
        if not search_success:
            print("❌ 차량 검색 실패로 테스트 중단")
            return
        
        # 4. 쿠폰 이력 조회 테스트
        history_success, coupon_history = await tester.test_coupon_history(vehicle_number)
        if not history_success:
            print("❌ 쿠폰 이력 조회 실패로 테스트 중단")
            return
        
        # 5. 쿠폰 적용 테스트 (올바른 로직 적용)
        store_config = tester.config_manager.get_store_config("A")
        coupons_to_apply = tester.decide_coupon_to_apply(
            coupon_history['my_history'],
            coupon_history['total_history'], 
            store_config.discount_types,
            coupon_history['available_coupons']
        )
        
        # 적용할 쿠폰이 있는지 확인
        total_to_apply = sum(count for count in coupons_to_apply.values() if count > 0)
        
        if total_to_apply > 0:
            print("\n=== 적용할 쿠폰 개수 ===")
            for coupon_name, count in coupons_to_apply.items():
                if count > 0:
                    print(f"{coupon_name}: {count}개")
            
            print(f"\n총 {total_to_apply}개 쿠폰을 적용합니다.")
            print("쿠폰 적용을 진행하시겠습니까? (y/n): ", end="")
            user_input = input().strip().lower()
            
            if user_input == 'y':
                # 계산된 쿠폰으로 적용 테스트
                test_applications = []
                for coupon_name, count in coupons_to_apply.items():
                    if count > 0:
                        test_applications.append({"name": coupon_name, "count": count})
                
                await tester.test_coupon_application(test_applications, coupon_history['available_coupons'])
            else:
                if logger.should_log_info():
                    logger.log_info("[전체 테스트] 쿠폰 적용 테스트 건너뜀")
        else:
            print("\n=== 적용할 쿠폰 없음 ===")
            print("이미 충분한 할인이 적용되었거나 적용 가능한 쿠폰이 없습니다.")
            if logger.should_log_info():
                logger.log_info("[전체 테스트] 적용할 쿠폰이 없어 테스트 건너뜀")
        
        if logger.should_log_info():
            logger.log_info("[전체 테스트] ✅ 모든 테스트 완료")
        
    except KeyboardInterrupt:
        if logger.should_log_info():
            logger.log_info("[전체 테스트] 사용자에 의한 중단")
        print("\n[중단] 사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        logger.log_error("A", "전체테스트", "FAIL_TEST", str(e))
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
    finally:
        # 리소스 정리
        await tester.cleanup()
        
        # 추가 대기 시간으로 AsyncIO 리소스 완전 정리
        import asyncio
        await asyncio.sleep(0.5)
        
        print("\n[완료] 테스트 종료")

if __name__ == "__main__":
    # 환경 변수 설정 (테스트 환경)
    os.environ['ENVIRONMENT'] = 'development'  # 개발 환경에서는 INFO 로그 허용
    
    # AsyncIO 정책 설정 (Windows에서 발생하는 문제 해결)
    import asyncio
    import sys
    
    if sys.platform.startswith('win'):
        # Windows에서 ProactorEventLoop 사용 시 발생하는 문제 해결
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(run_full_test())
    except KeyboardInterrupt:
        print("\n[중단] 사용자에 의한 테스트 중단")
    except Exception as e:
        print(f"\n[오류] 테스트 실행 중 오류 발생: {str(e)}")
    finally:
        # 최종 정리
        print("[시스템] 모든 리소스 정리 완료") 