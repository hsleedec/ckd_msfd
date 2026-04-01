import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    # [전략] 최신순 정렬 파라미터 추가 및 100건 조회
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'numOfRows': '100',
        'pageNo': '1'
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
        
        items_source = data.get('body', {}).get('items', [])
        items = [items_source] if isinstance(items_source, dict) else items_source

        found = []
        today = datetime.today()
        # 최근 7일 기준 (예: 20260325)
        limit_date = (today - timedelta(days=7)).strftime('%Y%m%d')

        if items:
            # API가 준 100개를 '허가일자' 기준으로 내림차순(최신순) 재정렬
            # (서버 솔팅이 불안정할 경우를 대비해 코드에서 한 번 더 정렬합니다)
            items.sort(key=lambda x: str(x.get('prmsn_dt', '')), reverse=True)

            for i in items:
                entp = str(i.get('entp_name', ''))
                item_name = str(i.get('item_name', ''))
                prmsn_dt = str(i.get('prmsn_dt', '')).replace('-', '') 

                # 필터링 조건: 업체명에 '종근당' 포함 + 날짜가 최근 7일 이내
                if '종근당' in entp and prmsn_dt >= limit_date:
                    found.append(f"✅ {entp}: {item_name} ({prmsn_dt})")
            
            # 3. 메시지 전송 로직
            if found:
                # 중복 제거
                found = sorted(list(set(found)), reverse=True)
                msg = f"🚀 [종근당 신규 허가 알림]\n(기준: {limit_date} 이후 최신순)\n\n" + "\n".join(found)
            else:
                # 1955년 데이터가 또 나오는지 확인하기 위해 샘플 추출
                latest_in_batch = items[0].get('prmsn_dt', '날짜없음')
                latest_entp = items[0].get('entp_name', '업체없음')
                
                msg = (f"🔔 최근 1주일 종근당 내역 없음\n"
                       f"━━━━━━━━━━━━━━━━━━\n"
                       f"📦 API 최상단 데이터:\n"
                       f"👉 {latest_entp} / {latest_in_batch}\n"
                       f"━━━━━━━━━━━━━━━━━━\n"
                       f"※ 이 날짜가 2026년이면 서버는 최신순으로 주고 있는 것입니다.")

        else:
            msg = "⚠️ 식약처 API에서 데이터를 응답하지 않았습니다."

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러 발생: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
