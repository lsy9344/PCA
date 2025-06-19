"""
B 매장 자동화 통합 테스트 스크립트
- 사용자 명령 없이 자동으로 실행
- 전체 플로우 테스트 (로그인 → 차량 검색 → 쿠폰 조회)
- 실패 시 상세 로그와 스크린샷 자동 생성
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import yaml
import logging

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로깅 설정 (유니코드 문제 해결)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'b_store_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# StreamHandler 인코딩 설정
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.stream = sys.stdout


class BStoreAutomatedTester:
    """B 매장 자동화 테스터 - 완전 자동 실행"""
    
    def __init__(self, headless=True):
        self.browser = None
        self.page = None
        self.playwright = None
        self.headless = headless
        self.config = self.load_config()
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'details': []
        }
    
    def load_config(self):
        """B 매장 설정 로드"""
        config_path = Path("infrastructure/config/store_configs/b_store_config.yaml")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return None
    
    async def initialize_browser(self):
        """브라우저 초기화"""
        try:
            logger.info("🌐 브라우저 초기화 중...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=500 if not self.headless else 0
            )
            self.page = await self.browser.new_page()
            self.page.set_default_timeout(30000)
            logger.info("✅ 브라우저 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"❌ 브라우저 초기화 실패: {e}")
            return False
    
    async def take_screenshot(self, filename_prefix="test"):
        """스크린샷 촬영"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{filename_prefix}_{timestamp}.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"📸 스크린샷 저장: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.warning(f"📸 스크린샷 저장 실패: {e}")
            return None
    
    def record_test_result(self, test_name, success, details=""):
        """테스트 결과 기록"""
        self.test_results['total_tests'] += 1
        if success:
            self.test_results['passed'] += 1
            logger.info(f"✅ {test_name}: 성공")
        else:
            self.test_results['failed'] += 1
            logger.error(f"❌ {test_name}: 실패 - {details}")
        
        self.test_results['details'].append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    async def test_navigation(self):
        """사이트 접속 테스트"""
        test_name = "사이트 접속"
        try:
            url = self.config['store']['website_url']
            logger.info(f"🔗 {url} 접속 중...")
            
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            
            # 페이지 제목 확인
            title = await self.page.title()
            if "호매실 로얄팰리스" in title:
                self.record_test_result(test_name, True, f"제목: {title}")
                return True
            else:
                self.record_test_result(test_name, False, f"예상하지 못한 제목: {title}")
                return False
                
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
            await self.take_screenshot("navigation_failed")
            return False
    
    async def test_login(self):
        """로그인 테스트"""
        test_name = "로그인"
        try:
            selectors = self.config['selectors']['login']
            login_info = self.config['login']
            
            logger.info("🔐 로그인 시도 중...")
            
            # 로그인 요소 존재 확인 (Playwright MCP에서 실제 동작했던 방식 사용)
            username_input = self.page.get_by_role('textbox', name='ID')
            password_input = self.page.get_by_role('textbox', name='PASSWORD')
            login_button = self.page.get_by_role('button', name='Submit')
            
            if await username_input.count() == 0:
                raise Exception("사용자명 입력란을 찾을 수 없음")
            if await password_input.count() == 0:
                raise Exception("비밀번호 입력란을 찾을 수 없음")
            if await login_button.count() == 0:
                raise Exception("로그인 버튼을 찾을 수 없음")
            
            # 로그인 정보 입력
            await username_input.fill(login_info['username'])
            await password_input.fill(login_info['password'])
            await login_button.click()
            
            # 페이지 변화 대기
            await self.page.wait_for_timeout(3000)
            
            # 로그인 성공 확인
            success_indicator = self.page.locator(selectors['login_success_indicator'])
            if await success_indicator.count() > 0:
                self.record_test_result(test_name, True, "로그인 성공 지표 발견")
                return True
            else:
                raise Exception("로그인 성공 지표를 찾을 수 없음")
                
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
            await self.take_screenshot("login_failed")
            return False
    
    async def test_popup_handling(self):
        """팝업 처리 테스트"""
        test_name = "팝업 처리"
        try:
            selectors = self.config['selectors']['popups']
            
            logger.info("🪟 팝업 처리 중...")
            
            # 안내 팝업 확인
            notice_popup = self.page.locator(selectors['notice_popup'])
            popup_count = await notice_popup.count()
            
            if popup_count > 0:
                logger.info(f"안내 팝업 {popup_count}개 발견")
                
                # OK 버튼 클릭
                ok_button = self.page.locator(selectors['ok_button'])
                if await ok_button.count() > 0:
                    await ok_button.click()
                    await self.page.wait_for_timeout(1000)
                    self.record_test_result(test_name, True, f"팝업 {popup_count}개 처리 완료")
                else:
                    self.record_test_result(test_name, False, "OK 버튼을 찾을 수 없음")
                    return False
            else:
                self.record_test_result(test_name, True, "처리할 팝업 없음")
            
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
            await self.take_screenshot("popup_failed")
            return False
    
    async def test_car_search_no_result(self):
        """차량 검색 테스트 (결과 없음)"""
        test_name = "차량 검색 (결과 없음)"
        try:
            selectors = self.config['selectors']['search']
            test_car_number = "12가3456"  # 테스트용 차량번호
            
            logger.info(f"🚗 차량번호 '{test_car_number}' 검색 중...")
            
            # 차량번호 입력 (Playwright MCP에서 실제 동작했던 방식 사용)
            car_input = self.page.get_by_role('textbox', name='차량번호')
            if await car_input.count() == 0:
                raise Exception("차량번호 입력란을 찾을 수 없음")
            
            await car_input.fill(test_car_number)
            
            # 검색 버튼 클릭
            search_button = self.page.get_by_role('button', name='검색')
            if await search_button.count() == 0:
                raise Exception("검색 버튼을 찾을 수 없음")
            
            await search_button.click()
            await self.page.wait_for_timeout(2000)
            
            # 결과 없음 메시지 확인
            no_result = self.page.locator(selectors['no_result_message'])
            if await no_result.count() > 0:
                # OK 버튼으로 팝업 닫기
                ok_button = self.page.locator('text=OK')
                if await ok_button.count() > 0:
                    await ok_button.click()
                    await self.page.wait_for_timeout(1000)
                
                self.record_test_result(test_name, True, "검색 결과 없음 메시지 정상 확인")
                return True
            else:
                self.record_test_result(test_name, False, "예상된 '검색 결과 없음' 메시지가 나타나지 않음")
                return False
                
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
            await self.take_screenshot("search_failed")
            return False
    
    async def test_discount_pages(self):
        """할인 관련 페이지 접근 테스트"""
        test_name = "할인 페이지 접근"
        try:
            logger.info("📄 할인 관련 페이지 테스트 중...")
            
            # 할인등록현황 페이지 테스트
            status_url = self.config['store']['website_url'].replace('/login', '/state/doViewMst')
            await self.page.goto(status_url)
            await self.page.wait_for_load_state('networkidle')
            
            # 할인 유형 드롭다운 확인 (더 구체적인 셀렉터 사용)
            dropdown = self.page.locator('select, combobox').first
            if await dropdown.count() > 0:
                # 옵션들 확인
                options = await dropdown.locator('option').all_text_contents()
                logger.info(f"발견된 할인 유형: {options}")
                
                expected_types = ["전체", "무료 1시간할인", "유료 30분할인", "유료 24시간할인"]
                if all(opt in str(options) for opt in expected_types):
                    self.record_test_result(test_name, True, f"할인 유형 확인: {options}")
                else:
                    self.record_test_result(test_name, False, f"예상하지 못한 할인 유형: {options}")
                    return False
            else:
                raise Exception("할인 유형 드롭다운을 찾을 수 없음")
            
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
            await self.take_screenshot("discount_pages_failed")
            return False
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("🧹 리소스 정리 완료")
        except Exception as e:
            logger.warning(f"⚠️ 리소스 정리 중 오류: {e}")
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        results = self.test_results
        
        print("\n" + "="*60)
        print("🅱️ B 매장 자동화 테스트 결과 요약")
        print("="*60)
        print(f"📊 전체 테스트: {results['total_tests']}개")
        print(f"✅ 성공: {results['passed']}개")
        print(f"❌ 실패: {results['failed']}개")
        print(f"📈 성공률: {(results['passed']/results['total_tests']*100):.1f}%" if results['total_tests'] > 0 else "0%")
        
        print("\n📋 세부 결과:")
        for detail in results['details']:
            status = "✅" if detail['success'] else "❌"
            print(f"  {status} {detail['test']}: {detail['details']}")
        
        print(f"\n📝 상세 로그: {logging.getLogger().handlers[0].baseFilename}")
        print("="*60)
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("🚀 B 매장 자동화 테스트 시작")
        
        if not self.config:
            logger.error("❌ 설정 파일 로드 실패로 테스트 중단")
            return
        
        try:
            # 1. 브라우저 초기화
            if not await self.initialize_browser():
                return
            
            # 2. 사이트 접속
            if not await self.test_navigation():
                return
            
            # 3. 로그인
            if not await self.test_login():
                return
            
            # 4. 팝업 처리
            await self.test_popup_handling()
            
            # 5. 차량 검색 (결과 없음)
            await self.test_car_search_no_result()
            
            # 6. 할인 페이지 접근
            await self.test_discount_pages()
            
            # 최종 스크린샷
            await self.take_screenshot("final_state")
            
        except Exception as e:
            logger.error(f"❌ 테스트 실행 중 치명적 오류: {e}")
            await self.take_screenshot("critical_error")
        
        finally:
            await self.cleanup()
            self.print_test_summary()


async def main():
    """메인 실행 함수"""
    print("🅱️ B 매장 자동화 테스트 - 자동 실행 모드")
    print("=" * 60)
    
    # 실행 모드 선택 (자동화를 위해 기본값 사용)
    headless = True  # 자동화 환경에서는 headless 모드 사용
    
    tester = BStoreAutomatedTester(headless=headless)
    await tester.run_all_tests()


if __name__ == "__main__":
    # 명령 없이 자동 실행
    asyncio.run(main()) 