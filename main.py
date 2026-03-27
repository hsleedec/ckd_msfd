import requests
import datetime
import os

def get_ckd_final_report():
    # 1. 환경 변수 로드
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    # 2. 날짜 설정 (어제 ~ 오늘)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=1)
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    # 3. 식약처 API 호출 (기간 검색 모드)
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'start_prmsn_dt': start_str,
        'end_prmsn_dt': end_str,
        'numOfRows': '200', # 2일치 데이터 넉넉히 수집
        'pageNo': '1'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        items = data.get('body', {}).get('items', [])
        
        # 4. 종근당 필터링 로직
        ckd_found = []
        if items:
            for item in items:
                entp = item.get('entp_name', '').replace(' ', '')
                # '종근당' 포함하되 '바이오'는 제외
                if '종근당' in entp and '바이오' not in entp:
                    name = item.get('item_name', '이름없음')
                    date = item.get('prmsn_dt', '날짜없음')
                    ckd_found.append(f"- {name} ({date})")

        # 5. 메시지 구성 및 전송
        if not ckd_found:
            # 데이터가 없을 때만 "대기 중" 메시지 발송
            msg = f"🔔 [{start_str}~{end_str}]\n종근당의 신규 허가 내역이 아직 API에 등록되지 않았습니다.\n(동기화 대기 중)"
        else:
            msg = f"🚀 [종근당 신규 허가 알림]\n" + "\n".join(ckd_found)

        # 텔레그램 전송
        send_url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(send_url, data={'chat_id': chat_id, 'text': msg})
        
    except Exception as e:
        # 에러 발생 시 로그 확인용 메시지
        err_msg = f"❌ 로봇 작동 에러: {str(e)}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': err_msg})

if __name__ == "__main__":
    get_ckd_final_report()
