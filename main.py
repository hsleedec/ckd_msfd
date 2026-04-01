import requests
import datetime
import os

def check_ckd_weekly():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    # 1. 날짜 설정 (오늘부터 7일 전까지)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=7)
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    # 2. 파라미터 설정 (1주일치 범위 지정)
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'start_prmsn_dt': start_str,
        'end_prmsn_dt': end_str,
        'numOfRows': '500', # 1주일치 전체 데이터를 넉넉히 가져옴
        'pageNo': '1'
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        response_data = res.json()
        
        # 데이터 구조 파악 및 추출
        items = response_data.get('body', {}).get('items', [])
        
        # 리스트가 아닌 단일 딕셔너리로 올 경우를 대비한 예외 처리
        if isinstance(items, dict):
            items = [items]

        # 3. 종근당 제품 필터링 (최신순 정렬)
        found = []
        if items:
            for i in items:
                entp = i.get('entp_name', '')
                if '종근당' in entp and '바이오' not in entp:
                    name = i.get('item_name', '이름없음')
                    dt = i.get('prmsn_dt', '날짜없음')
                    found.append(f"- {name} ({dt})")
        
        # 4. 메시지 구성
        if found:
            # 중복 제거 및 정렬
            found = sorted(list(set(found)), reverse=True)
            msg = f"🚀 [최근 1주일 종근당 허가 내역]\n기간: {start_str}~{end_str}\n\n" + "\n".join(found)
        else:
            # 데이터가 없을 때, API가 응답한 전체 건수를 표시하여 정상 작동 확인
            total_count = response_data.get('body', {}).get('totalCount', 0)
            msg = f"🔔 [{start_str}~{end_str}]\n해당 기간 내 종근당 허가 내역이 API에 없습니다.\n(조회된 전체 허가 건수: {total_count}건)"

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})
        
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러 발생: {str(e)}"})

if __name__ == "__main__":
    check_ckd_weekly()
