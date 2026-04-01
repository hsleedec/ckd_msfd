import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # 1. 전체 데이터 개수 확인 (마지막 페이지 계산)
        count_res = requests.get(url, params={'serviceKey': api_key, 'type': 'json', 'numOfRows': '1'}, timeout=30)
        total_count = count_res.json().get('body', {}).get('totalCount', 45000)
        last_page = (total_count // 100)
        
        found = []
        limit_date = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')

        # 2. 마지막 구역 200건(안전하게 2개 페이지) 조회
        for page in [last_page, last_page + 1]:
            params = {'serviceKey': api_key, 'type': 'json', 'numOfRows': '100', 'pageNo': str(page)}
            res = requests.get(url, params=params, timeout=30)
            items_raw = res.json().get('body', {}).get('items', [])
            items = [items_raw] if isinstance(items_raw, dict) else items_raw

            if items:
                for i in items:
                    # 필드명 수정: entp_eng_name (공식 명칭)
                    entp_eng = str(i.get('entp_eng_name', '')).upper() 
                    item_name = str(i.get('item_name', ''))
                    prmsn_dt = str(i.get('prmsn_dt', '')) # '2026-03-27' 형식 유지

                    # 검색 조건: 대문자로 통일해서 'CHONG KUN DANG' 포함 여부 확인
                    if 'CHONG KUN DANG' in entp_eng and prmsn_dt >= limit_date:
                        found.append(f"✅ {item_name} ({prmsn_dt})")

        # 3. 메시지 전송
        if found:
            msg = f"🚀 [CKD 영문명 기반 허가 알림]\n\n" + "\n".join(sorted(list(set(found)), reverse=True))
        else:
            # 작동 확인용 샘플
            msg = f"🔔 최근 1주일 종근당(CKD) 내역 없음\n(기준: {limit_date} 이후)"

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러 상세: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
