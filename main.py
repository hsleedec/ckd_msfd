import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    # 1. 환경변수 로드
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'numOfRows': '100',
        'pageNo': '1'
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        api_data = res.json()
        items = api_data.get('body', {}).get('items', [])

        if isinstance(items, dict):
            items = [items]

        found = []
        # 핵심: 식약처 형식(YYYYMMDD)과 똑같이 맞춥니다.
        today = datetime.today()
        one_week_ago = (today - timedelta(days=7)).strftime('%Y%m%d') 

        if items:
            for i in items:
                entp = i.get('entp_name', '')
                item_name = i.get('item_name', '')
                prmsn_dt = i.get('prmsn_dt', '') # 예: "20260327"
                
                # '종근당'이 포함되고, 날짜가 7일 전보다 크거나 같으면 수집
                if prmsn_dt >= one_week_ago and '종근당' in entp:
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        # 3. 메시지 구성
        if found:
            found = sorted(list(set(found)), reverse=True)
            msg = f"🚀 [종근당 신규 허가 알림]\n(최근 7일: {one_week_ago} 이후)\n\n" + "\n".join(found)
        else:
            msg = f"🔔 최근 1주일간 등록된 종근당 허가 내역이 없습니다.\n(기준일: {one_week_ago} 이후)"

        # 4. 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        error_msg = f"❌ 에러 발생: {str(e)}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': error_msg})

if __name__ == "__main__":
    check_pharm_approvals()
