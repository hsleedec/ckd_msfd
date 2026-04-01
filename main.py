import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    # 1. GitHub Secrets에서 환경변수 가져오기
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    # 2. 식약처 API 주소 및 파라미터 (최신 100건 조회)
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'numOfRows': '100',
        'pageNo': '1'
    }

    try:
        # API 호출
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
        items = data.get('body', {}).get('items', [])

        if isinstance(items, dict):  # 결과가 1건일 경우 예외처리
            items = [items]

        found = []
        today = datetime.today()  # 오늘 날짜
        one_week_ago = today - timedelta(days=7)  # 7일 전 날짜
        one_week_ago_str = one_week_ago.strftime('%Y-%m-%d')  # 7일 전 날짜를 'YYYY-MM-DD' 형식으로

        if items:
            for i in items:
                entp = i.get('entp_name', '')
                item_name = i.get('item_name', '')
                prmsn_dt = i.get('prmsn_dt', '')

                # 허가일이 최근 7일 이내에 해당하는지 확인
                if prmsn_dt >= one_week_ago_str and '종근당' in entp:
                    found.append(f"✅ {entp}: {item_name} ({prmsn_dt})")

        # 3. 메시지 구성
        if found:
            found = sorted(list(set(found)), reverse=True)
            msg = "🚀 [종근당 신규 허가 감지!]\n\n" + "\n".join(found)
        else:
            msg = f"🔔 최근 1주일 동안 허가된 종근당 제품이 없습니다."

        # 4. 텔레그램 전송
        response = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                                 data={'chat_id': chat_id, 'text': msg})
        print(response.json())  # 텔레그램 응답 로그 추가

    except Exception as e:
        error_msg = f"❌ 시스템 에러 발생: {str(e)}"
        response = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                                 data={'chat_id': chat_id, 'text': error_msg})
        print(response.json())  # 텔레그램 에러 응답 로그 추가
