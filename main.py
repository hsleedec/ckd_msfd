import requests
import os

def check_ckd_strictly():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    # [전략 변경] 날짜 검색을 빼고, 최신 등록 순으로 100개를 통째로 긁어옵니다.
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'numOfRows': '100', 
        'pageNo': '1'
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        items = res.json().get('body', {}).get('items', [])
        
        # 100개 중 종근당 제품만 추출
        found = [f"- {i.get('item_name')} ({i.get('prmsn_dt')})" for i in items if '종근당' in i.get('entp_name', '')]

        if found:
            msg = "🚀 [종근당 최신 허가 내역 발견!]\n" + "\n".join(found)
        else:
            # 못 찾았을 때, API 서버에 가장 마지막으로 등록된 제품이 뭔지 알려줍니다 (작동 확인용)
            last_item = items[0].get('item_name') if items else "없음"
            msg = f"🔔 아직 종근당 내역이 없습니다.\n(현재 API 최신 등록: {last_item})"

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})
        
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러: {str(e)}"})

if __name__ == "__main__":
    check_ckd_strictly()
