"""
AWS Lambda 시뮬레이션을 위한 로컬 웹훅 서버
구글폼 제출 시 이 서버가 요청을 받아 Lambda 핸들러를 실행합니다.
"""
import json
import asyncio
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from threading import Thread
import os
import sys

# 현재 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 환경 설정 로드
from utils.environment import load_environment_config, print_environment_info
config = load_environment_config()

# Lambda 핸들러 임포트
from interfaces.api.lambda_handler import lambda_handler

# 로깅 설정
log_level = getattr(logging, config['LOGGING']['LEVEL'], logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('local_lambda_server.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """구글폼 웹훅 엔드포인트 - AWS API Gateway 대체"""
    try:
        logger.info("=== 새로운 요청 수신 ===")
        
        # 요청 데이터 로깅
        data = request.get_json() or {}
        logger.info(f"수신 데이터: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # AWS Lambda 이벤트 형태로 변환
        lambda_event = {
            'body': json.dumps(data),
            'headers': dict(request.headers),
            'httpMethod': request.method,
            'path': request.path,
            'queryStringParameters': dict(request.args) or None,
            'requestContext': {
                'requestId': f'local-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'stage': 'local',
                'resourcePath': '/webhook'
            }
        }
        
        # Lambda 컨텍스트 시뮬레이션
        lambda_context = type('LambdaContext', (), {
            'function_name': 'parking-coupon-automation',
            'function_version': '1',
            'invoked_function_arn': 'arn:aws:lambda:local:123456789:function:parking-coupon-automation',
            'memory_limit_in_mb': '512',
            'remaining_time_in_millis': lambda: 300000,
            'request_id': lambda_event['requestContext']['requestId'],
            'log_group_name': '/aws/lambda/parking-coupon-automation',
            'log_stream_name': f"local/{datetime.now().strftime('%Y/%m/%d')}"
        })()
        
        logger.info("Lambda 핸들러 실행 시작...")
        
        # Lambda 핸들러 실행
        result = lambda_handler(lambda_event, lambda_context)
        
        logger.info(f"Lambda 핸들러 실행 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # Flask 응답 형태로 변환
        response_body = json.loads(result.get('body', '{}'))
        status_code = result.get('statusCode', 200)
        
        return jsonify(response_body), status_code
        
    except Exception as e:
        error_msg = f"서버 오류: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/test', methods=['GET', 'POST'])
def test_endpoint():
    """테스트용 엔드포인트"""
    if request.method == 'GET':
        return """
        <html>
        <head>
            <title>주차 쿠폰 자동화 테스트</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h2>주차 쿠폰 자동화 테스트</h2>
            <form method="POST">
                <p>
                    <label>매장 ID:</label><br>
                    <select name="store_id">
                        <option value="A">A 매장</option>
                        <option value="B">B 매장</option>
                    </select>
                </p>
                <p>
                    <label>차량번호:</label><br>
                    <input type="text" name="vehicle_number" placeholder="12가3456" required>
                </p>
                <p>
                    <input type="submit" value="자동화 실행">
                </p>
            </form>
        </body>
        </html>
        """
    else:
        # POST 요청 시 webhook으로 리다이렉트
        test_data = {
            'store_id': request.form.get('store_id'),
            'vehicle_number': request.form.get('vehicle_number')
        }
        
        # 내부적으로 webhook 호출
        from flask import current_app
        with current_app.test_client() as client:
            response = client.post('/webhook', 
                                 json=test_data,
                                 content_type='application/json')
            
        # JSON 응답을 한글이 제대로 표시되도록 포맷팅
        try:
            response_json = response.get_json()
            formatted_response = json.dumps(response_json, ensure_ascii=False, indent=2)
        except:
            formatted_response = response.get_data(as_text=True)
            
        return f"""
        <html>
        <head>
            <title>실행 결과</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h2>실행 결과</h2>
            <p><strong>상태 코드:</strong> {response.status_code}</p>
            <p><strong>응답:</strong></p>
            <pre>{formatted_response}</pre>
            <p><a href="/test">다시 테스트</a></p>
        </body>
        </html>
        """

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'local-lambda-server'
    })

@app.route('/', methods=['GET'])
def home():
    """홈 페이지"""
    return """
    <html>
    <head>
        <title>AWS Lambda 시뮬레이션 서버</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>AWS Lambda 시뮬레이션 서버</h1>
        <p>이 서버는 AWS Lambda 환경을 로컬에서 시뮬레이션합니다.</p>
        <ul>
            <li><a href="/test">테스트 페이지</a></li>
            <li><a href="/health">헬스 체크</a></li>
        </ul>
        
        <h2>사용법</h2>
        <p><strong>구글폼 웹훅 URL:</strong> http://localhost:5000/webhook</p>
        <p><strong>테스트 URL:</strong> http://localhost:5000/test</p>
        
        <h3>구글폼 설정 방법</h3>
        <ol>
            <li>구글폼 응답을 받을 때 이 URL로 POST 요청 보내기</li>
            <li>요청 본문에 store_id와 vehicle_number 포함</li>
        </ol>
        
        <h3>예시 요청</h3>
        <pre>
POST http://localhost:5000/webhook
Content-Type: application/json

{
    "store_id": "A",
    "vehicle_number": "12가3456"
}
        </pre>
    </body>
    </html>
    """

def run_server(host=None, port=None, debug=None):
    """서버 실행"""
    # 환경 설정에서 값 가져오기
    host = host or config['LOCAL_SERVER_HOST']
    port = port or config['LOCAL_SERVER_PORT']
    debug = debug if debug is not None else config['DEBUG']
    
    # 환경 정보 출력
    print_environment_info(config)
    
    logger.info(f"AWS Lambda 시뮬레이션 서버 시작: http://{host}:{port}")
    logger.info(f"웹훅 URL: http://{host}:{port}/webhook")
    logger.info(f"테스트 URL: http://{host}:{port}/test")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AWS Lambda 시뮬레이션 서버')
    parser.add_argument('--host', default='localhost', help='서버 호스트 (기본값: localhost)')
    parser.add_argument('--port', type=int, default=5000, help='서버 포트 (기본값: 5000)')
    parser.add_argument('--debug', action='store_true', help='디버그 모드 활성화')
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug) 