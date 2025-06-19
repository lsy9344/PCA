"""
B 매장 로그인 전용 테스트 스크립트
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class BStoreLoginTester:
    """B 매장 로그인 테스터"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        
        # B 매장 로그인 정보 (infrastructure/config/store_configs/b_store_config.yaml 참조)
        self.website_url = "https://a15878.parkingweb.kr/login"
        self.username = "215"
        self.password = "4318"
    
    async def initialize_browser(self, headless=False):
        """브라우저 초기화"""
        print(f"🌐 브라우저 초기화 (headless={headless})")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            slow_mo=1000 if not headless else 0  # 시각적 확인을 위해 천천히
        )
        self.page = await self.browser.new_page()
        
        # 기본 타임아웃 설정
        self.page.set_default_timeout(30000)
        
        print("✅ 브라우저 초기화 완료")
    
    async def navigate_to_site(self):
        """B 매장 사이트 접속"""
        print(f"🔗 B 매장 사이트 접속: {self.website_url}")
        
        await self.page.goto(self.website_url)
        await self.page.wait_for_load_state('networkidle')
        
        print("✅ 사이트 접속 완료")
        
        # 현재 페이지 URL 확인
        current_url = self.page.url
        print(f"📍 현재 URL: {current_url}")
    
    async def check_login_elements(self):
        """로그인 요소들 확인"""
        print("\n🔍 로그인 요소 확인 중...")
        
        # 사용자명 입력란 확인
        username_input = self.page.locator('#userId')
        username_count = await username_input.count()
        print(f"   - #userId 입력란: {'✅ 발견' if username_count > 0 else '❌ 없음'} ({username_count}개)")
        
        # 비밀번호 입력란 확인
        password_input = self.page.locator('#userPwd')
        password_count = await password_input.count()
        print(f"   - #userPwd 입력란: {'✅ 발견' if password_count > 0 else '❌ 없음'} ({password_count}개)")
        
        # 로그인 버튼 확인
        login_button = self.page.locator('input[type="submit"]')
        button_count = await login_button.count()
        print(f"   - input[type=\"submit\"] 버튼: {'✅ 발견' if button_count > 0 else '❌ 없음'} ({button_count}개)")
        
        # 페이지 HTML 일부 확인 (디버깅용)
        if username_count == 0 or password_count == 0 or button_count == 0:
            print("\n🔍 페이지에서 'input', 'userId', 'userPwd' 관련 요소들 검색:")
            
            # 모든 input 요소 확인
            all_inputs = await self.page.locator('input').all()
            print(f"   - 전체 input 요소: {len(all_inputs)}개")
            
            for i, input_elem in enumerate(all_inputs[:5]):  # 처음 5개만 확인
                try:
                    input_type = await input_elem.get_attribute('type') or 'text'
                    input_id = await input_elem.get_attribute('id') or 'no-id'
                    input_name = await input_elem.get_attribute('name') or 'no-name'
                    input_class = await input_elem.get_attribute('class') or 'no-class'
                    print(f"     [{i+1}] type={input_type}, id={input_id}, name={input_name}, class={input_class}")
                except Exception:
                    print(f"     [{i+1}] 요소 정보 읽기 실패")
        
        return username_count > 0 and password_count > 0 and button_count > 0
    
    async def perform_login(self):
        """로그인 수행"""
        print(f"\n🔐 로그인 수행 중...")
        print(f"   - 사용자명: {self.username}")
        print(f"   - 비밀번호: {'*' * len(self.password)}")
        
        try:
            # 사용자명 입력
            await self.page.fill('#userId', self.username)
            print("   ✅ 사용자명 입력 완료")
            
            # 비밀번호 입력
            await self.page.fill('#userPwd', self.password)
            print("   ✅ 비밀번호 입력 완료")
            
            # 로그인 버튼 클릭
            await self.page.click('input[type="submit"]')
            print("   ✅ 로그인 버튼 클릭 완료")
            
            # 페이지 변화 대기 (최대 10초)
            await self.page.wait_for_timeout(3000)
            
            return True
            
        except Exception as e:
            print(f"   ❌ 로그인 실패: {str(e)}")
            return False
    
    async def check_login_result(self):
        """로그인 결과 확인"""
        print(f"\n📊 로그인 결과 확인...")
        
        # 현재 URL 확인
        current_url = self.page.url
        print(f"   - 현재 URL: {current_url}")
        
        # 페이지 제목 확인
        try:
            title = await self.page.title()
            print(f"   - 페이지 제목: {title}")
        except Exception:
            print(f"   - 페이지 제목: 읽기 실패")
        
        # 로그인 성공 지표 확인
        success_indicators = [
            "div:has-text('안내')",  # 안내 팝업
            "text=안내",
            "button:has-text('OK')",
            "input[name='carNo']",  # 차량번호 입력란 (로그인 후 나타남)
            "text=차량번호"
        ]
        
        found_indicators = []
        for indicator in success_indicators:
            try:
                count = await self.page.locator(indicator).count()
                if count > 0:
                    found_indicators.append(f"{indicator} ({count}개)")
            except Exception:
                pass
        
        if found_indicators:
            print(f"   ✅ 로그인 성공 지표 발견:")
            for indicator in found_indicators:
                print(f"     - {indicator}")
        else:
            print(f"   ⚠️  로그인 성공 지표를 찾지 못했습니다")
        
        # 에러 메시지 확인
        error_indicators = [
            "text=로그인 실패",
            "text=아이디",
            "text=비밀번호", 
            "text=오류",
            "text=실패"
        ]
        
        found_errors = []
        for error in error_indicators:
            try:
                count = await self.page.locator(error).count()
                if count > 0:
                    found_errors.append(f"{error} ({count}개)")
            except Exception:
                pass
        
        if found_errors:
            print(f"   ❌ 에러 지표 발견:")
            for error in found_errors:
                print(f"     - {error}")
        
        return len(found_indicators) > 0 and len(found_errors) == 0
    
    async def handle_after_login_popup(self):
        """로그인 후 팝업 처리"""
        print(f"\n🪟 로그인 후 팝업 처리...")
        
        try:
            # 안내 팝업 확인
            notice_popup = self.page.locator('div').filter(has_text='안내')
            popup_count = await notice_popup.count()
            
            if popup_count > 0:
                print(f"   ✅ 안내 팝업 발견 ({popup_count}개)")
                
                # 첫 번째 안내 팝업 클릭
                await notice_popup.first.click()
                print(f"   ✅ 안내 팝업 클릭 완료")
                
                await self.page.wait_for_timeout(1000)
                
                # OK 버튼 찾아서 클릭
                ok_button = self.page.get_by_text('OK')
                ok_count = await ok_button.count()
                
                if ok_count > 0:
                    await ok_button.click()
                    print(f"   ✅ OK 버튼 클릭 완료")
                else:
                    print(f"   ⚠️  OK 버튼을 찾지 못했습니다")
                
                await self.page.wait_for_timeout(2000)
                return True
            else:
                print(f"   ℹ️  안내 팝업이 없습니다")
                return True
                
        except Exception as e:
            print(f"   ⚠️  팝업 처리 중 오류 (무시하고 계속): {str(e)}")
            return True
    
    async def take_screenshot(self, filename="b_store_login_test.png"):
        """스크린샷 촬영"""
        try:
            screenshot_path = Path(filename)
            await self.page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 스크린샷 저장: {screenshot_path.absolute()}")
        except Exception as e:
            print(f"📸 스크린샷 저장 실패: {str(e)}")
    
    async def cleanup(self):
        """리소스 정리"""
        print(f"\n🧹 리소스 정리 중...")
        
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("✅ 리소스 정리 완료")
        except Exception as e:
            print(f"⚠️  리소스 정리 중 오류: {str(e)}")


async def test_b_store_login():
    """B 매장 로그인 테스트 실행"""
    tester = BStoreLoginTester()
    
    try:
        print("=" * 60)
        print("🅱️  B 매장 로그인 테스트")
        print("=" * 60)
        
        # 브라우저 모드 선택
        headless_choice = input("Headless 모드로 실행하시겠습니까? (y/N): ").strip().lower()
        headless = headless_choice in ['y', 'yes']
        
        # 1. 브라우저 초기화
        await tester.initialize_browser(headless=headless)
        
        # 2. 사이트 접속
        await tester.navigate_to_site()
        
        # 3. 로그인 요소 확인
        elements_ok = await tester.check_login_elements()
        
        if not elements_ok:
            print("\n❌ 로그인 요소를 찾을 수 없습니다. 사이트 구조가 변경되었을 수 있습니다.")
            await tester.take_screenshot("b_store_login_elements_missing.png")
            return
        
        # 4. 로그인 수행
        login_ok = await tester.perform_login()
        
        if not login_ok:
            print("\n❌ 로그인 수행에 실패했습니다.")
            await tester.take_screenshot("b_store_login_failed.png")
            return
        
        # 5. 로그인 결과 확인
        result_ok = await tester.check_login_result()
        
        # 6. 로그인 후 팝업 처리
        await tester.handle_after_login_popup()
        
        # 7. 최종 상태 스크린샷
        await tester.take_screenshot("b_store_login_final.png")
        
        # 8. 결과 요약
        print("\n" + "=" * 60)
        print("📋 테스트 결과 요약")
        print("=" * 60)
        print(f"✅ 사이트 접속: 성공")
        print(f"{'✅' if elements_ok else '❌'} 로그인 요소 확인: {'성공' if elements_ok else '실패'}")
        print(f"{'✅' if login_ok else '❌'} 로그인 수행: {'성공' if login_ok else '실패'}")
        print(f"{'✅' if result_ok else '⚠️ '} 로그인 결과: {'성공' if result_ok else '확인 필요'}")
        
        if elements_ok and login_ok:
            print(f"\n🎉 B 매장 로그인 테스트 완료!")
            if not headless:
                input("\n브라우저 확인 후 Enter를 누르세요...")
        else:
            print(f"\n⚠️  일부 단계에서 문제가 발생했습니다. 스크린샷을 확인해주세요.")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
        await tester.take_screenshot("b_store_login_error.png")
        
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(test_b_store_login()) 