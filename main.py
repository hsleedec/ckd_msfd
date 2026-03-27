import requests
import datetime
import os

def get_hanmi_approvals():
    # 1. 날짜 설정 (오늘부터 29일 전까지, 총 30일치)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=29)
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    # 식약처 API 주소
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    
    # 검색 파라미터 (한 달 치 데이터 요청)
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'start_prmsn_dt': start_str,
        'end_prmsn_dt': end_str,
        'numOfRows': '500',          # 한 달 치니까 넉넉하게 500건 호출
        'pageNo': '1'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        items = data.get('body', {}).get('items', [])
        
        if not items:
            return f"❓ [{start_str} ~ {end_str}] 기간 내 API 데이터가 0건입니다. 식약처 서버 점검 중일 확률이 높습니다."

        # 한미약품 제품만 필터링
        target_list = []
        for item in items:
            entp_name = item.get('entp_name', '').replace(' ', '')
            # '한미약품' 글자가 들어간 모든 업체 검색
            if '한미약품' in entp_name:
                target_list.append(item)

        if not target_list:
            return f"✅ [{start_str} ~ {end_str}] 기간 중 '한미약품'의 신규 허가 건이 없습니다."

        # 메시지 구성
        msg = f"🏥 [최근 30일 한미약품 허가 현황]\n"
        # 날짜순 정렬 (최신순)
        target_list.sort(key=lambda x: x.get('prmsn_dt', ''), reverse=True)
        
        for i, product in enumerate(target_list, 1):
            name = product.get('item_name', '제품명 없음')
            date = product.get('prmsn_dt', '날짜 없음')
            msg += f"{i}. {name} ({date})\n"
        
        return msg

    except Exception as e:
        return f"❌ 에러 발생: {str(e)}"

def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    requests.post(url, data=payload)

if __name__ == "__main__":
    result = get_hanmi_approvals()
    send_telegram(result)
