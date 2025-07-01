/**
 * 구글폼 응답을 로컬 웹훅 서버로 전송하는 Apps Script
 * 
 * 설정 방법:
 * 1. 구글폼에서 Apps Script를 열기
 * 2. 이 코드를 붙여넣기
 * 3. WEBHOOK_URL을 실제 로컬 서버 주소로 변경
 * 4. 트리거 설정: onFormSubmit 함수를 폼 제출 시 실행되도록 설정
 */

// 로컬 웹훅 서버 URL (실제 IP 주소로 변경 필요)
const WEBHOOK_URL = 'http://YOUR_PC_IP:5000/webhook';

// 텔레그램 알림 설정 (선택사항)
const TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN';
const TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID';

/**
 * 구글폼 제출 시 실행되는 함수
 * 
 * 트리거 설정 방법:
 * 1. Apps Script 편집기에서 "트리거" 메뉴 클릭
 * 2. "트리거 추가" 클릭
 * 3. 함수: onFormSubmit
 * 4. 이벤트 소스: 스프레드시트에서
 * 5. 이벤트 유형: 양식 제출 시
 */
function onFormSubmit(e) {
  try {
    console.log('폼 제출 감지됨');
    
    // 제출된 응답 데이터 추출
    const responses = e.namedValues;
    console.log('응답 데이터:', responses);
    
    // 데이터 매핑 (폼 질문에 따라 수정 필요)
    let store_id = '';
    let vehicle_number = '';
    
    // 매장 선택 필드 처리
    if (responses['매장 선택'] && responses['매장 선택'][0]) {
      const storeSelection = responses['매장 선택'][0];
      if (storeSelection.includes('A') || storeSelection.includes('에이')) {
        store_id = 'A';
      } else if (storeSelection.includes('B') || storeSelection.includes('비')) {
        store_id = 'B';
      }
    }
    
    // 차량번호 필드 처리
    if (responses['차량번호'] && responses['차량번호'][0]) {
      vehicle_number = responses['차량번호'][0].trim();
    }
    
    // 필수 데이터 검증
    if (!store_id || !vehicle_number) {
      throw new Error(`필수 데이터 누락 - 매장: ${store_id}, 차량번호: ${vehicle_number}`);
    }
    
    // 웹훅 서버로 전송할 데이터
    const webhookData = {
      store_id: store_id,
      vehicle_number: vehicle_number,
      timestamp: new Date().toISOString(),
      source: 'google_form'
    };
    
    console.log('웹훅 전송 데이터:', webhookData);
    
    // 로컬 웹훅 서버로 HTTP POST 요청
    const response = sendToWebhook(webhookData);
    
    if (response.success) {
      console.log('웹훅 전송 성공:', response);
      
      // 성공 시 텔레그램 알림 (선택사항)
      if (TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID) {
        sendTelegramMessage(`✅ 자동화 요청 전송 완료\n매장: ${store_id}\n차량: ${vehicle_number}`);
      }
    } else {
      throw new Error(`웹훅 전송 실패: ${response.error}`);
    }
    
  } catch (error) {
    console.error('폼 처리 오류:', error);
    
    // 오류 시 텔레그램 알림
    if (TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID) {
      sendTelegramMessage(`❌ 폼 처리 오류: ${error.message}`);
    }
    
    // 오류를 다시 던져서 Apps Script 로그에 기록
    throw error;
  }
}

/**
 * 웹훅 서버로 데이터 전송
 */
function sendToWebhook(data) {
  try {
    const options = {
      'method': 'POST',
      'headers': {
        'Content-Type': 'application/json',
      },
      'payload': JSON.stringify(data)
    };
    
    console.log(`웹훅 요청 전송: ${WEBHOOK_URL}`);
    const response = UrlFetchApp.fetch(WEBHOOK_URL, options);
    
    const statusCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    console.log(`웹훅 응답 - 상태: ${statusCode}, 내용: ${responseText}`);
    
    if (statusCode >= 200 && statusCode < 300) {
      return {
        success: true,
        data: JSON.parse(responseText)
      };
    } else {
      return {
        success: false,
        error: `HTTP ${statusCode}: ${responseText}`
      };
    }
    
  } catch (error) {
    console.error('웹훅 전송 오류:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * 텔레그램 메시지 전송 (선택사항)
 */
function sendTelegramMessage(message) {
  try {
    if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
      console.log('텔레그램 설정이 없어 메시지를 보내지 않습니다.');
      return;
    }
    
    const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
    const payload = {
      'chat_id': TELEGRAM_CHAT_ID,
      'text': message,
      'parse_mode': 'HTML'
    };
    
    const options = {
      'method': 'POST',
      'headers': {
        'Content-Type': 'application/json',
      },
      'payload': JSON.stringify(payload)
    };
    
    UrlFetchApp.fetch(url, options);
    console.log('텔레그램 메시지 전송 완료');
    
  } catch (error) {
    console.error('텔레그램 메시지 전송 오류:', error);
  }
}

/**
 * 테스트 함수 - 수동 실행으로 테스트할 때 사용
 */
function testWebhook() {
  const testData = {
    store_id: 'A',
    vehicle_number: '12가3456',
    timestamp: new Date().toISOString(),
    source: 'manual_test'
  };
  
  console.log('테스트 데이터 전송:', testData);
  const result = sendToWebhook(testData);
  console.log('테스트 결과:', result);
  
  return result;
}

/**
 * 설정 확인 함수
 */
function checkConfiguration() {
  console.log('=== 설정 확인 ===');
  console.log('웹훅 URL:', WEBHOOK_URL);
  console.log('텔레그램 봇 토큰:', TELEGRAM_BOT_TOKEN ? '설정됨' : '설정 안됨');
  console.log('텔레그램 채팅 ID:', TELEGRAM_CHAT_ID ? '설정됨' : '설정 안됨');
  
  // 웹훅 서버 연결 테스트
  try {
    const response = UrlFetchApp.fetch(WEBHOOK_URL.replace('/webhook', '/health'));
    console.log('웹훅 서버 상태:', response.getContentText());
  } catch (error) {
    console.error('웹훅 서버 연결 실패:', error.message);
  }
} 