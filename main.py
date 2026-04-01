import requests
import os
from datetime import datetime, timedelta
import time

def check_pharm_approvals():
    # 1. GitHub Secrets에서 환경변수 가져오기
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    # 2. 식약처 API 주소 및 파라미터 (최신 100건 조회)
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'numOfRows': '100',
        'pageNo': '1'
    }

    try:
        # API 호출
        res = requests.get(url, params=params, timeout=30)
        
        # 식약처 API 응답 로그 추가
        api_data = res.json()
        print("식약처 API 응답:", api_data)  # 응답 데이터 확인

        items = api_data.get('body', {}).get('items', [])
        print("API에서 받은 데이터:", items)  # items 데이터 출력

        if isinstance(items, dict):  # 결과가 1건일 경우 예외처리
            items = [items]

        found = []
        today = datetime.today()  # 오늘 날짜
        one_week_ago = today - timedelta(days=7)  # 7일 전 날짜
        one_week_ago_str = one_week_ago.strftime('%Y-%m-%d')  # 7일 전 날짜를 'YYYY-MM-DD' 형식으로

        if items:
            for i in items:
                entp = i.get('entp_name', '')
                item_name = i.get('item_name', '')
                prmsn_dt = i.get('prmsn_dt', '')
                
                # 날짜 필터링
                print(f"허가일: {prmsn_dt}, 오늘: {today.strftime('%Y-%m-%d')}, 7일 전: {one_week_ago_str}")

                # 허가일이 최근 7일 이내에 해당하는지 확인
                if prmsn_dt >= one_week_ago_str and '종근당' in entp:
                    found.append(f"✅ {entp}: {item_name} ({prmsn_dt})")

        # 3. 메시지 구성
        if found:
            found = sorted(list(set(found)), reverse=True)
            msg = "🚀 [종근당 신규 허가 감지!]\n\n" + "\n".join(found)
        else:
            msg = f"🔔 최근 1주일 동안 허가된 종근당 제품이 없습니다."

        # 4. 텔레그램 전송
        response = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                                 data={'chat_id': chat_id, 'text': msg})
        
        # 텔레그램 응답 로그 추가
        response_data = response.json()
        print("텔레그램 응답:", response_data)  # 텔레그램 응답 확인

        # 속도 제한에 걸릴 경우 일정 시간 대기
        if response_data.get('error_code') == 429:  # Too Many Requests 에러 확인
            print("속도 제한에 걸림. 대기 중...")
            time.sleep(10)  # 10초 대기 후 재시도

    except Exception as e:
        error_msg = f"❌ 시스템 에러 발생: {str(e)}"
        response = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                                 data={'chat_id': chat_id, 'text': error_msg})
        print("텔레그램 에러 응답:", response.json())  # 텔레그램 에러 응답 로그 추가
