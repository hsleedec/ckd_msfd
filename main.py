import requests
import os

def check_ckd_capture():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    # [설계] 날짜/업체명 검색어를 빼고 '최신순 100건'만 요청해서 코드 내에서 직접 찾습니다.
    # 이렇게 해야 식약처 서버의 검색 버그를 피할 수 있습니다.
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'numOfRows': '100', 
        'pageNo': '1'
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
        items = data.get('body', {}).get('items', [])
        
        if isinstance(items, dict):
            items = [items]

        found = []
        if items:
            for i in items:
                entp = i.get('entp_name', '')
                item_name = i.get('item_name', '')
                prmsn_dt = i.get('prmsn_dt', '')
                
                # '종근당' 글자가 들어있으면 무조건 수집 (주식회사 여부 상관없음)
                if '종근당' in entp:
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        if found:
            # 중복 제거 및 정렬
            found = sorted(list(set(found)), reverse=True)
            msg = "🚀 [종근당 신규 허가 확인!]\n\n" + "\n".join(found)
        else:
            # 여전히 없다면 API 서버가 홈페이지보다 느린 것입니다.
            # 확인을 위해 API상 가장 최신 제품의 날짜를 찍어줍니다.
            latest_date = items[0].get('prmsn_dt') if items else "알수없음"
            msg = f"🔔 아직 API 서버에 종근당 데이터가 올라오지 않았습니다.\n(현재 API 최신 데이터 날짜: {latest_date})\n\n※ 홈페이지(안전나라)와 API 서버는 시차가 발생할 수 있습니다."

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})
        
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 시스템 에러: {str(e)}"})

if __name__ == "__main__":
    check_ckd_capture()
