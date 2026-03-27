import requests
import datetime
import os
import sys

# 1. 깃허브 설정(Secrets)에서 안전하게 정보를 가져옵니다.
DATA_GO_KR_API_KEY = os.environ.get('DATA_GO_KR_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_jonggeundang_products():
    # 오늘 날짜 (YYYYMMDD)
    today = datetime.datetime.now().strftime('%Y%m%d')
    
    # 식약처 품목허가 정보 조회 서비스 API (OpenAPI)
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService05/getDrugPrdtPrmsnInq05'
    
    params = {
        'serviceKey': DATA_GO_KR_API_KEY,
        'type': 'json',
        'prmsn_dt': today,        # 허가일자: 오늘
        'entp_name': '(주)종근당', # 업체명 정확히 일치 시킴
        'pageNo': '1',
        'numOfRows': '100'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        # 한글 깨짐 방지
        response.encoding = 'utf-8'
        data = response.json()
        
        items = data.get('body', {}).get('items', [])
        
        # 실제 데이터가 있는지 확인 (리스트가 비어있지 않은지)
        if not items:
            return f"[{today}] (주)종근당의 신규 허가 내역이 없습니다."

        message = f"🔔 [(주)종근당 신규 허가 알림]\n📅 날짜: {today}\n\n"
        
        for item in items:
            # API 검색 결과 중 업체명이 정확히 '(주)종근당'인 것만 다시 한 번 검증
            if item.get('entp_name') == '(주)종근당':
                name = item.get('item_name')
                prdt_type = item.get('etc_otc_code') # 전문/일반 구분
                message += f"✅ 제품명: {name}\n"
                message += f"📦 구분: {prdt_type}\n"
                message += f"🔗 상세링크: https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail?itemSeq={item.get('item_seq')}\n"
                message += f"------------------\n"
        
        return message

    except Exception as e:
        return f"❌ 오류 발생: {str(e)}"

def send_telegram(text):
    if not text: return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

if __name__ == "__main__":
    # 필수 환경변수 체크
    if not all([DATA_GO_KR_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        print("환경변수 설정이 누락되었습니다. GitHub Settings를 확인하세요.")
        sys.exit(1)
        
    result_msg = get_jonggeundang_products()
    send_telegram(result_msg)