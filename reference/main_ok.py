"""
주차 쿠폰 자동화 Lambda 핸들러
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError
from utils.logger import logger
from utils.discount_logic import is_weekday, decide_coupon_to_apply
from config import STORE_CONFIGS, PLAYWRIGHT_CONFIG
import re
import sys
import aiohttp

# 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN = '7694000458:AAFDa7szcGRjJJUy8cU_eJnU9MPgqsWnkmk'
TELEGRAM_CHAT_ID = '6968094848'

async def send_telegram_message(error_message: str, car_number: str):
    """텔레그램 봇으로 에러 메시지 전송"""
    try:
        current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        message = f"""
🚨 쿠폰 자동화 실패 알림 🚨

1. 실패 원인: {error_message}
2. 실패 차량번호: {car_number}
3. 실패 시간: {current_time}
"""
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }) as response:
                if response.status == 200:
                    logger.info("[텔레그램] 실패 알림 전송 성공")
                else:
                    logger.error(f"[텔레그램] 실패 알림 전송 실패: {await response.text()}")
    except Exception as e:
        logger.error(f"[텔레그램] 메시지 전송 중 에러 발생: {str(e)}")

async def handle_popups(page):
    """팝업 처리"""
    # 1. 인트로 팝업 닫기
    try:
        await page.click("#skip")
        logger.info("[팝업처리] 인트로 팝업 닫기 성공")
    except Exception as e:
        logger.error(f"[팝업처리] 인트로 팝업 닫기 실패: {str(e)}")

    # 2. 공지 팝업 닫기
    try:
        await page.click("#popupCancel")
        logger.info("[팝업처리] 공지 팝업 닫기 성공")
    except Exception as e:
        logger.error(f"[팝업처리] 공지 팝업 닫기 실패: {str(e)}")

    # 3. 튜토리얼/기타 팝업 닫기 (여러 방식 병행)
    try:
        # ESC 키로 닫기 시도
        await page.keyboard.press("Escape")
        logger.info("[팝업처리] ESC 키로 팝업 닫기 시도")
    except Exception as e:
        logger.error(f"[팝업처리] ESC 키 닫기 실패: {str(e)}")

    try:
        # '닫기' 텍스트로 닫기 시도
        close_button = page.locator('button:has-text("닫기")')
        if await close_button.count() > 0:
            await close_button.click()
            logger.info("[팝업처리] '닫기' 버튼으로 팝업 닫기 성공")
    except Exception as e:
        logger.error(f"[팝업처리] '닫기' 버튼 닫기 실패: {str(e)}")

async def login(page, username: str, password: str):
    """로그인 처리"""
    try:
        # 로그인 폼 입력
        await page.fill("#id", username)
        await page.fill("#password", password)
        await page.click("#login")
        
        # 로그인 성공 확인 (차량번호 입력란이 보이는지)
        await page.wait_for_selector("#carNumber", timeout=PLAYWRIGHT_CONFIG["TIMEOUT"])
        logger.info("[로그인] 로그인 성공")

        # 로그인 성공 후: 첫 번째 팝업 닫기기 클릭 (#gohome)
        try:
            await page.click('#gohome')
            logger.info("[로그인 후] 첫 번째 팝업 닫기 버튼 클릭 성공")
        except Exception as e:
            logger.error(f"[로그인 후] #gohome 버튼 클릭 실패: {str(e)}")

        # 두 번째 팝업 닫기기 버튼 클릭 (#start)
        try:
            await page.click('#start')
            logger.info("[로그인 후] 두 번째 팝업 닫기 버튼 클릭 성공")
        except Exception as e:
            logger.error(f"[로그인 후] #start 버튼 클릭 실패: {str(e)}")

    except TimeoutError:
        logger.error("[로그인] 로그인 실패: 차량번호 입력란이 나타나지 않음")
        raise
    except Exception as e:
        logger.error(f"[로그인] 로그인 실패: {str(e)}")
        raise

def notify_no_car_found_trigger(car_number: str):
    """
    검색된 차량이 없을 때 호출되는 트리거 함수.
    (향후 Slack 등 외부 알림 연동용)
    """
    logger.info(f"[트리거] 검색된 차량 없음 알림 트리거: {car_number}")
    # TODO: 외부 메신저 연동 시 이 함수에서 처리

async def search_car(page, car_number: str):
    """차량 검색"""
    try:
        # 차량번호 입력
        await page.fill("#carNumber", car_number)
        logger.info('[차량검색] 차량 번호 입력 성공')
        
        # 검색 버튼 클릭 (여러 셀렉터 시도)
        try:
            await page.click('button[name="search"]')
        except:
            try:
                await page.click('.btn-search')
            except:
                await page.click('button:has-text("검색")')
        
        # 검색 결과 대기
        await page.wait_for_timeout(1000)  # 결과 로딩 대기
        
        # [추가] #parkName의 텍스트가 '검색된 차량이 없습니다.'인지 확인
        try:
            park_name_elem = page.locator('#parkName')
            if await park_name_elem.count() > 0:
                park_name_text = await park_name_elem.inner_text()
                if '검색된 차량이 없습니다.' in park_name_text:
                    logger.error('[차량검색] #parkName: 검색된 차량이 없습니다. 프로세스 종료')
                    notify_no_car_found_trigger(car_number)
                    import sys
                    sys.exit(0)
        except Exception as e:
            logger.error(f'[차량검색] #parkName 텍스트 확인 실패: {str(e)}')
        
        # 기존: 검색 결과 확인
        no_result = page.locator('text="검색된 차량이 없습니다"')
        if await no_result.count() > 0:
            logger.error("[차량검색] 검색 결과 없음")
            raise Exception("검색된 차량이 없습니다")
            
        # 차량 선택 버튼 클릭
        try:
            # 버튼을 우선적으로 클릭
            await page.click('#next')
            logger.info('[차량검색] 차량 선택 버튼 클릭 성공')
            # 다음 페이지 로딩을 위해 5초 대기
            await page.wait_for_timeout(5000)  # 5000ms = 5초
        except Exception as e1:
            try:
                await page.click('button:has-text("차량 선택")')
                logger.info('[차량검색] button:has-text("차량 선택") 버튼 클릭 성공')
                # 다음 페이지 로딩을 위해 5초 대기
                await page.wait_for_timeout(3000)  # 3000ms = 3초
            except Exception as e2:
                logger.error(f'[차량검색] 차량 선택 버튼 클릭 실패: #next: {str(e1)}, has-text: {str(e2)}')
                raise
            
        logger.info(f"[차량검색] 차량번호 {car_number} 검색 및 선택 후 5초뒤 페이지 로딩 성공")
    except Exception as e:
        logger.error(f"[차량검색] 검색 실패: {str(e)}")
        raise

async def get_coupon_history(page, store_config):
    """
    쿠폰 보유 상태, 매장 이력, 전체 이력을 모두 dict로 반환
    """
    try:
        discount_types = store_config['DISCOUNT_TYPES']
        discount_info = {name: {'car': 0, 'total': 0} for name in discount_types.values()}

        # productList 테이블 로드 대기
        await page.wait_for_selector('#productList tr', timeout=PLAYWRIGHT_CONFIG["TIMEOUT"])
        
        # 쿠폰 없음 체크
        empty_message = await page.locator('#productList td.empty').count()
        if empty_message > 0:
            logger.info("[쿠폰상태] 보유한 쿠폰이 없습니다")
            return discount_info, {name: 0 for name in discount_types.values()}, {name: 0 for name in discount_types.values()}

        # 쿠폰이 있는 경우 파싱
        rows = await page.locator('#productList tr').all()
        for row in rows:
            try:
                cells = await row.locator('td').all()
                if len(cells) >= 2:
                    name = (await cells[0].inner_text()).strip()
                    count_text = (await cells[1].inner_text()).strip()
                    
                    for discount_name in discount_types.values():
                        if discount_name in name:  # 부분 포함 매칭
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

        # 2. 우리 매장 쿠폰 내역 (#myDcList)
        my_history = {name: 0 for name in discount_types.values()}
        try:
            my_dc_rows = await page.locator('#myDcList tr').all()
            for row in my_dc_rows:
                cells = await row.locator('td').all()
                if len(cells) >= 2:
                    name = (await cells[0].inner_text()).strip()
                    count_text = (await cells[1].inner_text()).strip()
                    
                    for discount_name in discount_types.values():
                        if discount_name in name:  # 부분 포함 매칭
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
            
        # 3. 전체 쿠폰 이력 (#allDcList)
        total_history = {name: 0 for name in discount_types.values()}
        try:
            total_rows = await page.locator('#allDcList tr').all()
            for row in total_rows:
                cells = await row.locator('td').all()
                if len(cells) >= 2:
                    name = (await cells[0].inner_text()).strip()
                    count_text = (await cells[1].inner_text()).strip()
                    
                    for discount_name in discount_types.values():
                        if discount_name in name:  # 부분 포함 매칭
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
        logger.error(f"[쿠폰조회] 이력 조회 실패: {str(e)}")
        return (
            {name: {'car': 0, 'total': 0} for name in discount_types.values()},
            {name: 0 for name in discount_types.values()},
            {name: 0 for name in discount_types.values()}
        )

async def apply_coupons(page, coupons_to_apply: dict):
    """쿠폰 적용"""
    try:
        for coupon_name, count in coupons_to_apply.items():
            if count > 0:
                # 해당 쿠폰의 행 찾기
                rows = await page.locator("#productList tr").all()
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
                                    await page.wait_for_selector('#popupOk', timeout=PLAYWRIGHT_CONFIG["TIMEOUT"])
                                    await page.click('#popupOk')
                                    logger.info("[쿠폰적용] 첫 번째 확인 팝업 처리 성공")
                                    await page.wait_for_timeout(500)  # 팝업 닫힘 대기
                                except Exception as e:
                                    logger.error(f"[쿠폰적용] 첫 번째 확인 팝업 처리 실패: {str(e)}")
                                
                                # 3. 두 번째 확인 팝업 처리
                                try:
                                    await page.wait_for_selector('#popupOk', timeout=PLAYWRIGHT_CONFIG["TIMEOUT"])
                                    await page.click('#popupOk')
                                    logger.info("[쿠폰적용] 두 번째 확인 팝업 처리 성공")
                                    await page.wait_for_timeout(500)  # 팝업 닫힘 대기
                                except Exception as e:
                                    logger.error(f"[쿠폰적용] 두 번째 확인 팝업 처리 실패: {str(e)}")
                            
                            logger.info(f"[쿠폰적용] {coupon_name} {count}개 적용 성공")
                        else:
                            logger.error(f"[쿠폰적용] {coupon_name} 적용 버튼을 찾을 수 없음")
                        break
    except Exception as e:
        logger.error(f"[쿠폰적용] 적용 실패: {str(e)}")
        raise

async def process_car(car_number: str, store_config: dict):
    """단일 차량 처리 함수"""
    try:
        async with async_playwright() as p:
            # Lambda 환경에 맞는 브라우저 설정
            browser = await p.chromium.launch(
                headless=PLAYWRIGHT_CONFIG["HEADLESS"],
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context()
            page = await context.new_page()
            
            # 기본 타임아웃 설정
            page.set_default_timeout(PLAYWRIGHT_CONFIG["TIMEOUT"])
            
            try:
                # 사이트 접속
                await page.goto(store_config['URL'])
                logger.info("[접속] 사이트 접속 성공")
                
                # 팝업 처리
                await handle_popups(page)
                
                # 로그인
                await login(page, store_config['USERNAME'], store_config['PASSWORD'])
                
                # 차량 검색
                await search_car(page, car_number)
                
                # 쿠폰 현황 파악
                discount_info, my_history, total_history = await get_coupon_history(page, store_config)
                
                # 쿠폰 적용 결정
                coupons_to_apply = decide_coupon_to_apply(
                    discount_info,
                    my_history,
                    total_history,
                    store_config
                )
                
                # 쿠폰 적용
                if coupons_to_apply:
                    await apply_coupons(page, coupons_to_apply)
                    logger.info(f"[쿠폰적용] {car_number} 차량 쿠폰 적용 완료")
                else:
                    logger.info(f"[쿠폰적용] {car_number} 차량 적용할 쿠폰 없음")
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': 'Success',
                        'car_number': car_number,
                        'applied_coupons': coupons_to_apply
                    })
                }
                
            except Exception as e:
                error_message = str(e)
                logger.error(f"[실행오류] {error_message}")
                await send_telegram_message(error_message, car_number)
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'message': 'Error',
                        'error': error_message,
                        'car_number': car_number
                    })
                }
            finally:
                await browser.close()
                
    except Exception as e:
        error_message = f"브라우저 실행 오류: {str(e)}"
        logger.error(error_message)
        await send_telegram_message(error_message, car_number)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error',
                'error': error_message,
                'car_number': car_number
            })
        }

def lambda_handler(event, context):
    """
    AWS Lambda 핸들러 함수
    """
    try:
        # 이벤트에서 차량번호와 매장 정보 추출
        body = json.loads(event.get('body', '{}'))
        car_number = body.get('car_number')
        store_name = body.get('store_name')
        
        if not car_number or not store_name:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Missing required parameters',
                    'required': ['car_number', 'store_name']
                })
            }
            
        # 매장 설정 가져오기
        store_config = STORE_CONFIGS.get(store_name)
        if not store_config:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': f'Invalid store name: {store_name}'
                })
            }
            
        # 비동기 함수 실행
        result = asyncio.run(process_car(car_number, store_config))
        return result
        
    except Exception as e:
        error_message = f"Lambda 핸들러 오류: {str(e)}"
        logger.error(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error',
                'error': error_message
            })
        }

# 로컬 테스트를 위한 실행 코드
if __name__ == "__main__":
    import argparse
    
    # 명령행 인자 파서 설정
    parser = argparse.ArgumentParser(description='주차 쿠폰 자동화 테스트')
    parser.add_argument('car_number', help='차량번호')
    parser.add_argument('--store', default='A', help='매장 이름 (기본값: A)')
    args = parser.parse_args()
    
    # 테스트용 이벤트 생성
    test_event = {
        'body': json.dumps({
            'car_number': args.car_number,
            'store_name': args.store
        })
    }
    
    # Lambda 핸들러 실행
    result = lambda_handler(test_event, None)
    
    # 결과 출력
    print("\n실행 결과:")
    print(json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False))

