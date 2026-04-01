import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    # API 주소 (버전 07 확인)
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
        
        # [데이터 추출 로직 보강]
        # body나 items가 없을 경우를 대비해 단계별로 안전하게 접근
        body = data.get('body', {})
        items_source = body.get('items', [])
        
        # 식약처 API 특유의 변덕(1건일 때 리스트가 아님) 처리
        items = []
        if isinstance(items_source, dict):
            items = [items_source]
        elif isinstance(items_source, list):
            items = items_source

        found = []
        today = datetime.today()
        # 8자리 숫자 기준 (하이픈 제거)
        one_week_ago_str = (today - timedelta(days=7)).strftime('%Y%m%d') 

        if items:
            for i in items:
                # 필드명이 대소문자 섞여 나오거나 비어있을 경우 대비
                entp = str(i.get('entp_name') or i.get('ENTP_NAME') or '')
                item_name = str(i.get('item_name') or i.get('ITEM_NAME') or '제품명없음')
                prmsn_dt = str(i.get('prmsn_dt') or i.get('PRMSN_DT') or '').replace('-', '') 
                
                # '종근당'이 포함되고 날짜 조건 만족 시
                if '종근당' in entp and prmsn_dt >= one_week_ago_str:
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        # 3. 메시지 구성
        if found:
            found = sorted(list(set(found)), reverse=True)
            msg = f"🚀 [종근당 신규 허가 발견!]\n(기준: {one_week_ago_str} 이후)\n\n" + "\n".join(found)
        else:
            # 작동 확인용: 데이터가 있긴 한데 종근당이 없는 건지 확인
            if items:
                first_item = items[0].get('item_name') or items[0].get('ITEM_NAME') or '이름모를제품'
                first_date = items[0].get('prmsn_dt') or items[0].get('PRMSN_DT') or '날짜모름'
                msg = f"🔔 최근 1주일 종근당 내역 없음\n(API 최신 등록: {first_item} / {first_date})"
            else:
                msg = "⚠️ 식약처 API 응답에 데이터가 비어있습니다. (서버 동기화 지연 중)"

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        # 에러 발생 시 로그를 상세히 찍어 텔레그램으로 전송
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': f"❌ 에러 상세: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
