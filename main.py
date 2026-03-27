import requests
import datetime
import os
import sys
from urllib.parse import unquote

# 1. 환경 변수 로드
# 환경변수에 등록할 때 인증키가 이미 인코딩되어 있다면 unquote로 풀어줘야 합니다.
DATA_GO_KR_API_KEY = unquote(os.environ.get('DATA_GO_KR_API_KEY', ''))
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_jonggeundang_products():
    today = datetime.datetime.now().strftime('%Y%m%d')
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService05/getDrugPrdtPrmsnInq05'
    
    # 한글 업체명과 인증키를 안전하게 파라미터로 구성
    params = {
        'serviceKey': DATA_GO_KR_API_KEY,
        'type': 'json',
        'prmsn_dt': today,
        'entp_name': '(주)종근당',
        'pageNo': '1',
        'numOfRows': '100'
    }

    try:
        # API 호출
        response = requests.get(url, params=params, timeout=30)
        
        # 1차 체크: 서버 응답 코드가 200(성공)인지 확인
        if response.status_code != 200:
            return f"❌ API 서버 연결 실패 (에러코드: {response.status_code})"

        # 2차 체크: 응답 내용이 XML(에러메시지)인지 JSON인지 확인
        content = response.text.strip()
        if content.startswith('<'):
            if 'SERVICE_KEY_IS_NOT_REGISTERED_ERROR' in content:
                return "❌ 오류: 공공데이터 API 인증키가 등록되지 않았거나 잘못되었습니다."
            return f"❌ API 서버에서 XML 에러를 보냈습니다:\n{content[:100]}"

        # JSON 파싱
        data = response.json()
        items = data.get('body', {}).get('items', [])
        
        if not items:
            return f"[{today}] (주)종근당의 신규 허가 내역이 없습니다."

        message = f"🔔 [(주)종근당 신규 허가 알림]\n📅 날짜: {today}\n\n"
        for item in items:
            if item.get('entp_name') == '(주)종근당':
                message += f"✅ 제품명: {item.get('item_name')}\n"
                message += f"📦 구분: {item.get('etc_otc_code')}\n"
                message += f"🔗 상세: https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail?itemSeq={item.get('item_seq')}\n"
                message += f"------------------\n"
        return message

    except Exception as e:
        return f"❌ 실행 중 오류 발생: {str(e)}"

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
    requests.post(url, data=payload)

if __name__ == "__main__":
    if not all([DATA_GO_KR_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        send_telegram("❌ 환경변수(Secrets) 설정이 누락되었습니다.")
        sys.exit(1)
    
    result_msg = get_jonggeundang_products()
    send_telegram(result_msg)
