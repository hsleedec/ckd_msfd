import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # 1. 먼저 전체 데이터가 몇 건인지 확인합니다.
        check_res = requests.get(url, params={'serviceKey': api_key, 'type': 'json', 'numOfRows': '1'}, timeout=30)
        total_count = check_res.json().get('body', {}).get('totalCount', 44000)
        
        # 2. 마지막 페이지 번호를 계산합니다. (한 페이지당 100건 기준)
        last_page = (total_count // 100) + 1
        
        # 3. 마지막 페이지(최신 데이터)를 가져옵니다.
        params = {
            'serviceKey': api_key,
            'type': 'json',
            'numOfRows': '100',
            'pageNo': str(last_page)
        }
        
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
        items_source = data.get('body', {}).get('items', [])
        items = [items_source] if isinstance(items_source, dict) else items_source

        found = []
        today = datetime.today()
        limit_date = (today - timedelta(days=7)).strftime('%Y%m%d')

        if items:
            # 마지막 페이지 데이터를 날짜 역순으로 정렬
            items.sort(key=lambda x: str(x.get('prmsn_dt', '')), reverse=True)

            for i in items:
                entp = str(i.get('entp_name', ''))
                item_name = str(i.get('item_name', ''))
                raw_dt = str(i.get('prmsn_dt', '')).replace('-', '')

                if '종근당' in entp and raw_dt >= limit_date:
                    found.append(f"✅ {item_name} ({raw_dt})")

        # 4. 결과 보고
        if found:
            found = sorted(list(set(found)), reverse=True)
            msg = f"🚀 [종근당 신규 허가 확인!]\n(마지막 페이지 역추적 완료)\n\n" + "\n".join(found)
        else:
            # 작동 확인용 샘플 (이제 1955년이 아니라 2026년 데이터가 찍혀야 함)
            sample_item = items[0].get('item_name', '제품명없음') if items else "데이터없음"
            sample_date = items[0].get('prmsn_dt', '날짜없음') if items else "날짜없음"
            
            msg = (f"🔔 최근 1주일 종근당 내역 없음\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"📦 API 최신 구역 제품:\n"
                   f"👉 {sample_item}\n"
                   f"📅 허가일자: {sample_date}\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"※ 이 날짜가 2026년 3월이면 로봇은 이제 정확한 위치에 있는 겁니다.")

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러 발생: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
