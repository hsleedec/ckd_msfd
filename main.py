import requests
import datetime
import os

def get_ckd_approvals():
    # 1. 날짜 설정 (오늘부터 2일 전까지, 총 3일치)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=2)
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    # 식약처 API 주소 (07 버전)
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    
    # 검색 파라미터 (시작일~종료일 범위 지정)
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'start_prmsn_dt': start_str, # 시작일 추가
        'end_prmsn_dt': end_str,     # 종료일 추가
        'numOfRows': '100',          # 3일치니까 넉넉하게 100건
        'pageNo': '1'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        items = data.get('body', {}).get('items', [])
        
        if not items:
            return f"❓ [{start_str} ~ {end_str}] 기간 내에 식약처 API에 등록된 데이터가 아예 없습니다. (서버 동기화 지연 중)"

        # 종근당 제품만 필터링
        ckd_list = []
        for item in items:
            entp_name = item.get('entp_name', '').replace(' ', '')
            # 종근당은 포함하되 바이오는 제외 (전공 분야 집중!)
            if '종근당' in entp_name and '바이오' not in entp_name:
                ckd_list.append(item)

        if not ckd_list:
            return f"✅ [{start_str} ~ {end_str}] 기간 중 종근당의 신규 허가 건이 없습니다."

        # 메시지 구성
        msg = f"🚀 [최근 3일 종근당 허가 현황]\n"
        for i, product in enumerate(ckd_list, 1):
            name = product.get('item_name', '제품명 없음')
            date = product.get('prmsn_dt', '날짜 없음')
            msg += f"{i}. {name} ({date})\n"
        
        return msg

    except Exception as e:
        return f"❌ 에러 발생: {str(e)}"

# 텔레그램 전송부 (기존과 동일)
def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    requests.post(url, data=payload)

if __name__ == "__main__":
    result = get_ckd_approvals()
    send_telegram(result)
