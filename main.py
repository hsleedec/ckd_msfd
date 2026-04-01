import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # 1. 전체 데이터가 몇 건인지 먼저 확인 (마지막 페이지를 알기 위함)
        count_res = requests.get(url, params={'serviceKey': api_key, 'type': 'json', 'numOfRows': '1'}, timeout=30)
        total_count = count_res.json().get('body', {}).get('totalCount', 44000)
        
        # 2. 마지막 페이지 번호 계산 (100건씩 볼 때 가장 마지막 페이지)
        last_page = (total_count // 100) + 1
        
        # 3. 마지막 페이지(가장 최신 데이터 구역) 조회
        params = {
            'serviceKey': api_key,
            'type': 'json',
            'numOfRows': '100',
            'pageNo': str(last_page)
        }
        
        res = requests.get(url, params=params, timeout=30)
        items_data = res.json().get('body', {}).get('items', [])
        items = [items_data] if isinstance(items_data, dict) else items_data

        found = []
        today = datetime.today()
        limit_date = (today - timedelta(days=7)).strftime('%Y%m%d')

        if items:
            # 가져온 데이터를 날짜 최신순으로 다시 정렬
            items.sort(key=lambda x: str(x.get('prmsn_dt', '')), reverse=True)

            for i in items:
                entp = str(i.get('entp_name', ''))
                item_name = str(i.get('item_name', ''))
                prmsn_dt = str(i.get('prmsn_dt', '')).replace('-', '')

                # 최근 7일 이내 + 종근당 포함 여부 체크
                if '종근당' in entp and prmsn_dt >= limit_date:
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        # 4. 텔레그램 전송
        if found:
            msg = f"🚀 [종근당 신규 허가 확인!]\n\n" + "\n".join(sorted(list(set(found)), reverse=True))
        else:
            # 2026년 데이터가 맞는지 확인용 샘플
            sample_name = items[0].get('item_name', '제품명없음') if items else "데이터없음"
            sample_date = items[0].get('prmsn_dt', '날짜없음') if items else "날짜없음"
            msg = (f"🔔 최근 1주일 종근당 내역 없음\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"📦 API 최신 구역 제품:\n"
                   f"👉 {sample_name}\n"
                   f"📅 허가일자: {sample_date}\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"※ 이 날짜가 2026년 3월이면 로봇이 정확한 위치를 찾은 겁니다.")

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
