"""
수동 테스트 스크립트
사용자가 직접 실행하여 다양한 시나리오를 테스트할 수 있습니다.
"""
import requests
import json

def manual_api_test():
    """수동 API 테스트"""
    print("🔧 수동 API 테스트")
    print("="*40)
    
    # 사용자 입력 받기
    print("\n📝 테스트할 데이터를 입력하세요:")
    store_id = input("매장 ID (A 또는 B): ").strip().upper()
    vehicle_number = input("차량번호 (예: 12가3456): ").strip()
    
    # 주말 여부 선택
    is_weekend_input = input("주말 테스트인가요? (y/N): ").strip().lower()
    is_weekend = is_weekend_input in ['y', 'yes', '네', 'ㅇ']
    
    # API 호출 데이터 구성
    test_data = {
        "store_id": store_id,
        "vehicle_number": vehicle_number
    }
    
    if is_weekend:
        test_data["is_weekend"] = True
    
    print(f"\n📤 전송할 데이터: {json.dumps(test_data, ensure_ascii=False)}")
    print("⏳ API 호출 중...")
    
    try:
        # API 호출
        response = requests.post(
            "http://localhost:5000/webhook",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n📥 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 성공!")
            print(f"📊 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print("❌ 실패!")
            print(f"🔍 오류 내용: {response.text}")
            
    except Exception as e:
        print(f"🚨 오류 발생: {str(e)}")

def test_different_scenarios():
    """다양한 시나리오 테스트"""
    print("\n🎭 다양한 시나리오 테스트")
    print("="*40)
    
    scenarios = [
        {"name": "평일 A매장 기본", "store_id": "A", "vehicle_number": "11가1111"},
        {"name": "주말 A매장", "store_id": "A", "vehicle_number": "22나2222", "is_weekend": True},
        {"name": "B매장 테스트", "store_id": "B", "vehicle_number": "33다3333"},
        {"name": "잘못된 매장 ID", "store_id": "C", "vehicle_number": "44라4444"},
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 30)
        
        # is_weekend 키가 없으면 제거
        test_data = {k: v for k, v in scenario.items() if k != 'name'}
        
        try:
            response = requests.post(
                "http://localhost:5000/webhook",
                json=test_data,
                timeout=10
            )
            
            print(f"상태: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"결과: {result.get('success', '알 수 없음')}")
                if 'error_message' in result:
                    print(f"오류: {result['error_message']}")
            else:
                print(f"실패: {response.text[:100]}...")
                
        except Exception as e:
            print(f"오류: {str(e)}")

def check_server_status():
    """서버 상태 확인"""
    print("\n🔍 서버 상태 확인")
    print("="*30)
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        
        if response.status_code == 200:
            health = response.json()
            print("✅ 서버 정상 작동")
            print(f"서비스: {health.get('service', '알 수 없음')}")
            print(f"상태: {health.get('status', '알 수 없음')}")
            print(f"시간: {health.get('timestamp', '알 수 없음')}")
            return True
        else:
            print(f"❌ 서버 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"🚨 서버 연결 실패: {str(e)}")
        print("\n💡 해결 방법:")
        print("1. 다른 터미널에서 서버 실행: python local_lambda_server.py")
        print("2. 방화벽 설정 확인")
        print("3. 포트 5000이 사용 중인지 확인")
        return False

if __name__ == "__main__":
    print("🧪 수동 테스트 도구")
    print("="*50)
    
    # 서버 상태 확인
    if not check_server_status():
        exit(1)
    
    while True:
        print("\n📋 테스트 메뉴:")
        print("1. 수동 API 테스트 (직접 입력)")
        print("2. 다양한 시나리오 테스트 (자동)")
        print("3. 서버 상태 재확인")
        print("4. 종료")
        
        choice = input("\n선택하세요 (1-4): ").strip()
        
        if choice == "1":
            manual_api_test()
        elif choice == "2":
            test_different_scenarios()
        elif choice == "3":
            check_server_status()
        elif choice == "4":
            print("👋 테스트 종료!")
            break
        else:
            print("❌ 잘못된 선택입니다. 1-4 중에서 선택하세요.") 