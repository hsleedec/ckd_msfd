import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    # [전략] 날짜 필터를 빼고 '최신 100건'을 가져온 뒤 코드에서 직접 거릅니다.
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'numOfRows': '100',
        'pageNo': '1'
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
        
        # 1. 데이터 구조 안전하게 추출
        body = data.get('body', {})
        items_data = body.get('items', [])
        
        # 식약처 API 특유의 변덕(1건일 때 리스트가 아님) 처리
        items = []
        if isinstance(items_data, dict):
            items = [items_data]
        elif isinstance(items_data, list):
            items = items_data

        found = []
        today = datetime.today()
        # 최근 7일 기준 (형식: 20260325)
        limit_date = (today - timedelta(days=7)).strftime('%Y%m%d')

        if items:
            # 허가일자(prmsn_dt) 기준으로 내림차순 정렬
            items.sort(key=lambda x: str(x.get('prmsn_dt', '')), reverse=True)

            for i in items:
                # 업체명, 제품명, 날짜를 모든 가능성(대소문자 등)을 열고 추출
                entp = str(i.get('entp_name') or i.get('ENTP_NAME') or '')
                item_name = str(i.get('item_name') or i.get('ITEM_NAME') or '제품명확인불가')
                raw_dt = str(i.get('prmsn_dt') or i.get('PRMSN_DT') or '').replace('-', '')

                # [필터링] '종근당' 포함 여부와 날짜 체크
                if '종근당' in entp and raw_dt >= limit_date:
                    found.append(f"✅ {entp}: {item_name} ({raw_dt})")
            
            # 2. 결과 메시지 작성
            if found:
                found = sorted(list(set(found)), reverse=True)
                msg = f"🚀 [종근당 신규 허가 확인!]\n(최근 7일 데이터)\n\n" + "\n".join(found)
            else:
                # 종근당이 없을 때, 현재 API가 보고 있는 가장 최신 제품 하나를 명시
                first_item = items[0].get('item_name') or items[0].get('ITEM_NAME') or '이름모를제품'
                first_date = items[0].get('prmsn_dt') or items[0].get('PRMSN_DT') or '날짜모름'
                msg = (f"🔔 최근 1주일 종근당 내역 없음\n"
                       f"━━━━━━━━━━━━━━━━━━\n"
                       f"📦 API 최상단 제품:\n"
                       f"👉 {first_item}\n"
                       f"📅 허가일자: {first_date}\n"
                       f"━━━━━━━━━━━━━━━━━━\n"
                       f"※ 이 날짜가 2026년 3월 말이면 로봇은 정상 작동 중입니다.")
        else:
            msg = "⚠️ 식약처 API 서버가 현재 빈 데이터를 응답하고 있습니다. (잠시 후 재시도 필요)"

        # 3. 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        # 에러 발생 시 상세 내용을 텔레그램으로 전송
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': f"❌ 에러 상세: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
