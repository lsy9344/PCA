"""
로컬 환경 설정 테스트 스크립트
"""
import requests
import json
import time
import sys
import os

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.environment import load_environment_config, get_pc_ip_address

def test_webhook_server():
    """웹훅 서버 테스트"""
    config = load_environment_config()
    
    # 서버 주소들
    localhost_base = f"http://localhost:{config['LOCAL_SERVER_PORT']}"
    
    # PC IP 주소로도 테스트
    pc_ip = get_pc_ip_address()
    network_base = f"http://{pc_ip}:{config['LOCAL_SERVER_PORT']}"
    
    print("=== 로컬 웹훅 서버 테스트 ===")
    print(f"로컬 주소: {localhost_base}")
    print(f"네트워크 주소: {network_base}")
    print()
    
    # 테스트할 엔드포인트들
    endpoints = [
        ('/health', 'GET'),
        ('/', 'GET'),
        ('/test', 'GET')
    ]
    
    test_results = []
    
    for endpoint, method in endpoints:
        print(f"테스트 중: {method} {endpoint}")
        
        # localhost 테스트
        try:
            url = localhost_base + endpoint
            if method == 'GET':
                response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"  ✓ localhost: 성공 ({response.status_code})")
                test_results.append(('localhost', endpoint, True))
            else:
                print(f"  ✗ localhost: 실패 ({response.status_code})")
                test_results.append(('localhost', endpoint, False))
                
        except Exception as e:
            print(f"  ✗ localhost: 연결 실패 - {str(e)}")
            test_results.append(('localhost', endpoint, False))
        
        # 네트워크 IP 테스트 (localhost와 다른 경우만)
        if pc_ip != 'localhost':
            try:
                url = network_base + endpoint
                if method == 'GET':
                    response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    print(f"  ✓ 네트워크: 성공 ({response.status_code})")
                    test_results.append(('network', endpoint, True))
                else:
                    print(f"  ✗ 네트워크: 실패 ({response.status_code})")
                    test_results.append(('network', endpoint, False))
                    
            except Exception as e:
                print(f"  ✗ 네트워크: 연결 실패 - {str(e)}")
                test_results.append(('network', endpoint, False))
        
        print()
    
    return test_results

def test_webhook_endpoint():
    """웹훅 엔드포인트 테스트"""
    config = load_environment_config()
    
    print("=== 웹훅 엔드포인트 테스트 ===")
    
    # 테스트 데이터
    test_data = {
        'store_id': 'A',
        'vehicle_number': '12가3456'
    }
    
    webhook_url = f"http://localhost:{config['LOCAL_SERVER_PORT']}/webhook"
    
    try:
        print(f"웹훅 URL: {webhook_url}")
        print(f"테스트 데이터: {json.dumps(test_data, ensure_ascii=False)}")
        
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60  # Lambda 실행 시간을 고려해 길게 설정
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        
        try:
            response_data = response.json()
            print("응답 내용:")
            print(json.dumps(response_data, ensure_ascii=False, indent=2))
            
            if response.status_code == 200:
                print("✓ 웹훅 테스트 성공!")
                return True
            else:
                print("✗ 웹훅 테스트 실패!")
                return False
                
        except json.JSONDecodeError:
            print("응답 내용 (텍스트):")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"✗ 웹훅 테스트 실패: {str(e)}")
        return False

def check_dependencies():
    """필수 의존성 확인"""
    print("=== 의존성 확인 ===")
    
    dependencies = [
        ('flask', 'Flask'),
        ('requests', 'requests'),
        ('playwright', 'Playwright'),
        ('dotenv', 'python-dotenv')
    ]
    
    all_ok = True
    
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {package_name}: 설치됨")
        except ImportError:
            print(f"✗ {package_name}: 설치 필요 - pip install {package_name}")
            all_ok = False
    
    print()
    return all_ok

def check_environment_config():
    """환경 설정 확인"""
    print("=== 환경 설정 확인 ===")
    
    try:
        config = load_environment_config()
        
        # 필수 설정 확인
        required_configs = [
            ('STORE_A.URL', config['STORE_A']['URL']),
            ('STORE_A.USERNAME', config['STORE_A']['USERNAME']),
            ('STORE_A.PASSWORD', config['STORE_A']['PASSWORD']),
        ]
        
        all_configured = True
        
        for config_name, config_value in required_configs:
            if config_value and config_value != 'your_username' and config_value != 'your_password':
                print(f"✓ {config_name}: 설정됨")
            else:
                print(f"✗ {config_name}: 설정 필요")
                all_configured = False
        
        # 선택적 설정 확인
        optional_configs = [
            ('텔레그램 봇 토큰', config['TELEGRAM']['BOT_TOKEN']),
            ('텔레그램 채팅 ID', config['TELEGRAM']['CHAT_ID']),
        ]
        
        for config_name, config_value in optional_configs:
            if config_value and config_value != 'your_telegram_bot_token' and config_value != 'your_telegram_chat_id':
                print(f"✓ {config_name}: 설정됨")
            else:
                print(f"○ {config_name}: 설정 안됨 (선택사항)")
        
        print()
        return all_configured
        
    except Exception as e:
        print(f"✗ 환경 설정 로드 실패: {str(e)}")
        return False

def main():
    """메인 테스트 함수"""
    print("🔍 AWS Lambda 로컬 시뮬레이션 환경 테스트")
    print("=" * 50)
    print()
    
    # 1. 의존성 확인
    deps_ok = check_dependencies()
    
    # 2. 환경 설정 확인
    config_ok = check_environment_config()
    
    if not deps_ok or not config_ok:
        print("❌ 사전 요구사항이 충족되지 않았습니다.")
        print("필요한 패키지를 설치하고 환경 설정을 완료한 후 다시 시도하세요.")
        return False
    
    # 3. 서버 연결 테스트
    print("서버 테스트를 시작합니다...")
    print("(서버가 실행 중인지 확인하세요: python local_lambda_server.py)")
    print()
    
    time.sleep(1)
    
    # 기본 엔드포인트 테스트
    server_results = test_webhook_server()
    
    # 웹훅 테스트 (선택사항)
    print()
    user_input = input("웹훅 엔드포인트 테스트를 실행하시겠습니까? (y/N): ")
    if user_input.lower() in ['y', 'yes']:
        webhook_ok = test_webhook_endpoint()
    else:
        webhook_ok = True
        print("웹훅 테스트를 건너뜁니다.")
    
    # 결과 요약
    print()
    print("=" * 50)
    print("📋 테스트 결과 요약")
    print("=" * 50)
    
    success_count = sum(1 for _, _, success in server_results if success)
    total_count = len(server_results)
    
    print(f"기본 엔드포인트: {success_count}/{total_count} 성공")
    
    if webhook_ok:
        print("✅ 전체 테스트 통과!")
        print()
        print("🎉 이제 구글폼과 연동할 준비가 되었습니다!")
        print("자세한 설정 방법은 LOCAL_SETUP_GUIDE.md를 참고하세요.")
        return True
    else:
        print("❌ 일부 테스트 실패")
        print("문제를 해결한 후 다시 시도하세요.")
        return False

if __name__ == '__main__':
    main() 