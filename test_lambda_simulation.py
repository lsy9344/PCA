"""
AWS Lambda 시뮬레이션 테스트
로컬에서 AWS Lambda 환경을 시뮬레이션하여 전체 자동화 프로세스를 테스트합니다.
"""
import requests
import json
import time

def test_lambda_webhook():
    """Lambda 웹훅 테스트"""
    print("🚀 AWS Lambda 시뮬레이션 테스트 시작")
    print("="*60)
    
    # 서버 URL
    webhook_url = "http://localhost:5000/webhook"
    
    # 테스트 데이터 (Google Form에서 전송될 데이터 시뮬레이션)
    test_cases = [
        {
            "name": "기본 테스트 - A매장",
            "data": {
                "store_id": "A",
                "vehicle_number": "12가3456"
            }
        },
        {
            "name": "주말 테스트 - A매장", 
            "data": {
                "store_id": "A",
                "vehicle_number": "34나5678",
                "is_weekend": True
            }
        },
        {
            "name": "기본 테스트 - B매장",
            "data": {
                "store_id": "B", 
                "vehicle_number": "56다7890"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 케이스 {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # AWS API Gateway + Lambda 호출 시뮬레이션
            print(f"📤 요청 데이터: {json.dumps(test_case['data'], ensure_ascii=False)}")
            
            response = requests.post(
                webhook_url,
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"📥 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 성공: {json.dumps(result, ensure_ascii=False, indent=2)}")
            else:
                print(f"❌ 실패: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"🚨 네트워크 오류: {str(e)}")
        except Exception as e:
            print(f"🚨 예상치 못한 오류: {str(e)}")
        
        print("\n" + "="*60)
        time.sleep(1)  # 테스트 간격

def test_lambda_health_check():
    """Lambda 서버 헬스체크"""
    print("\n🔍 Lambda 서버 헬스체크")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 서버 상태: {health_data['status']}")
            print(f"🕐 응답 시간: {health_data['timestamp']}")
            print(f"🏠 서비스: {health_data['service']}")
            return True
        else:
            print(f"❌ 헬스체크 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"🚨 헬스체크 오류: {str(e)}")
        return False

def test_lambda_test_page():
    """Lambda 테스트 페이지 접근"""
    print("\n🌐 Lambda 테스트 페이지 확인")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:5000/test", timeout=5)
        
        if response.status_code == 200:
            print("✅ 테스트 페이지 접근 성공")
            print("🔗 브라우저에서 http://localhost:5000/test 확인 가능")
            return True
        else:
            print(f"❌ 테스트 페이지 접근 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"🚨 테스트 페이지 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎯 AWS Lambda 로컬 시뮬레이션 테스트")
    print("=" * 60)
    
    # 1. 헬스체크
    if not test_lambda_health_check():
        print("\n❌ 서버가 실행되지 않았습니다. 먼저 서버를 시작하세요:")
        print("python local_lambda_server.py")
        exit(1)
    
    # 2. 테스트 페이지 확인
    test_lambda_test_page()
    
    # 3. 웹훅 테스트 실행
    test_lambda_webhook()
    
    print("\n🎉 AWS Lambda 시뮬레이션 테스트 완료!")
    print("\n💡 추가 테스트 방법:")
    print("1. 브라우저에서 http://localhost:5000/test 접속")
    print("2. Google Apps Script에서 webhook URL 테스트")
    print("3. Postman/curl로 직접 API 호출") 