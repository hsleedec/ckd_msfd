import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    # 환경변수로부터 인증키와 토큰을 가져옴
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # 최근 7일 날짜 계산
        today = datetime.today()
        limit_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')

        found = []  # 종근당 제품을 담을 리스트

        # API 호출: 최신 데이터 100건씩 가져오기
        params = {
            'serviceKey': api_key,
            'type': 'json',
            'numOfRows': '100',  # 한 번에 100건씩 가져오기
            'pageNo': '1'  # 첫 번째 페이지부터 시작
        }

        res = requests.get(url, params=params, timeout=30)
        data = res.json().get('body', {}).get('items', [])

        # 만약 데이터가 있다면, 종근당 제품만 필터링
        if data:
            # 종근당 제품만 필터링
            for item in data:
                entp_name = str(item.get('entp_name_eng', '')).upper()  # 영문 업체명
                item_name = str(item.get('item_name', ''))  # 제품명
                prmsn_dt = str(item.get('prmsn_dt', ''))  # 허가일

                # 종근당 제품 필터링 (영문명으로 'CHONG KUN DANG'을 확인)
                if 'CHONG KUN DANG' in entp_name and prmsn_dt >= limit_date:
                    found.append(f"✅ {item_name} / {prmsn_dt}")
            
            # 최신순으로 정렬
            found = sorted(found, key=lambda x: x.split(' / ')[-1], reverse=True)

        # 텔레그램 메시지 구성
        if found:
            msg = f"🚀 [종근당 신규 허가 알림]\n\n" + "\n".join(found)
        else:
            msg = f"🔔 최근 1주일 종근당 내역 없음\n(식약처 API DB 동기화 대기 중...)"

        # 텔레그램 메시지 전송
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 시스템 에러: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
