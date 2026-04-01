import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # 1. 전체 개수 확인해서 마지막 페이지 계산
        count_res = requests.get(url, params={'serviceKey': api_key, 'type': 'json', 'numOfRows': '1'}, timeout=30)
        total_count = count_res.json().get('body', {}).get('totalCount', 45000)
        last_page = (total_count // 100)
        
        found = []
        limit_date = (datetime.today() - timedelta(days=7)).strftime('%Y%m%d')

        # 2. 마지막 2개 페이지(200건)를 샅샅이 뒤집니다. (10개만 보는 지피티와 급이 다름)
        for page in [last_page, last_page + 1]:
            params = {'serviceKey': api_key, 'type': 'json', 'numOfRows': '100', 'pageNo': str(page)}
            res = requests.get(url, params=params, timeout=30)
            items_data = res.json().get('body', {}).get('items', [])
            items = [items_data] if isinstance(items_data, dict) else items_data

            if items:
                for i in items:
                    # 필드명 수정: entp_eng_name (이게 진짜임)
                    entp_eng = str(i.get('entp_eng_name', '')).upper() 
                    item_name = str(i.get('item_name', ''))
                    # 하이픈 제거해서 20260327 형식으로 비교
                    raw_dt = str(i.get('prmsn_dt', '')).replace('-', '') 

                    # 영문명에 'CHONG KUN DANG'이 들어있으면 무조건 낚음
                    if 'CHONG KUN DANG' in entp_eng and raw_dt >= limit_date:
                        found.append(f"✅ {item_name} ({raw_dt})")

        # 3. 텔레그램 전송
        if found:
            msg = f"🚀 [종근당 신규 허가 감지!]\n\n" + "\n".join(sorted(list(set(found)), reverse=True))
        else:
            msg = f"🔔 최근 1주일 종근당 내역 없음\n(식약처 API DB 동기화 대기 중...)"

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
