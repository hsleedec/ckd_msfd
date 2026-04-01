import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
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
        data = res.json()
        
        # [구조 정밀 분석] 데이터가 어디에 숨어있든 찾아냅니다.
        body = data.get('body', {})
        items_data = body.get('items', [])
        
        # 식약처 API 특유의 '1건일 때 리스트가 아닌 딕셔너리' 에러 방지
        if isinstance(items_data, dict):
            items = [items_data]
        elif isinstance(items_data, list):
            items = items_data
        else:
            items = []

        found = []
        today = datetime.today()
        # 하이픈 제거한 8자리 숫자 기준 (예: 20260325)
        one_week_ago_str = (today - timedelta(days=7)).strftime('%Y%m%d') 

        if items:
            for i in items:
                # 업체명과 제품명 추출 (데이터가 비어있을 경우 대비)
                entp = str(i.get('entp_name', ''))
                item_name = str(i.get('item_name', ''))
                prmsn_dt = str(i.get('prmsn_dt', '')).replace('-', '') 
                
                # '종근당'이 포함되어 있고 날짜 기준 충족 시
                if '종근당' in entp and prmsn_dt >= one_week_ago_str:
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        # 3. 메시지 구성
        if found:
            found = sorted(list(set(found)), reverse=True)
            msg = f"🚀 [종근당 신규 허가 발견!]\n(기준: {one_week_ago_str} 이후)\n\n" + "\n".join(found)
        else:
            # 작동 확인용: API 상의 첫 번째 아이템 정보를 강제로 출력
            if items:
                sample = items[0]
                s_name = sample.get('item_name', '제품명없음')
                s_date = sample.get('prmsn_dt', '날짜없음')
                msg = f"🔔 최근 1주일 종근당 내역 없음\n(API 최신 등록: {s_name} / {s_date})"
            else:
                msg = "⚠️ 식약처 API가 빈 데이터를 보냈습니다. (서버 동기화 중일 가능성)"

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': f"❌ 에러 발생: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
