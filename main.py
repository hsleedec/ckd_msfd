import requests
import datetime
import os
import sys
import time

# 1. 환경 변수 로드 (GitHub Secrets에 등록된 값)
DATA_GO_KR_API_KEY = os.environ.get('DATA_GO_KR_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_ckd_products():
    """
    식약처 API에서 오늘자 허가 품목을 가져와 (주)종근당 제품만 필터링합니다.
    """
    today = datetime.datetime.now().strftime('%Y%m%d')
    # 최신 Service07 버전을 사용합니다.
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    # 업체명을 파라미터에 넣지 않고 전체를 가져와서 필터링 (누락 방지)
    params = {
        'serviceKey': DATA_GO_KR_API_KEY,
        'type': 'json',
        'prmsn_dt': today,
        'pageNo': '1',
        'numOfRows': '500' 
    }

    try:
        # 서버 불안정을 대비해 최대 2번 시도
        for i in range(2):
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                break
            time.sleep(3)
        
        if response.status_code != 200:
            return f"❌ 식약처 서버 연결 실패 (코드: {response.status_code})"

        data = response.json()
        items = data.get('body', {}).get('items', [])
        
        # API 서버에 아직 데이터가 안 올라온 경우
        if not items:
            return f"✅ [{today}] 식약처 API에 아직 오늘자 데이터가 업데이트되지 않았습니다. (보통 홈페이지보다 1~2시간 늦습니다.)"

        ckd_list = []
        for item in items:
            # 업체명에서 공백을 제거하고 비교 (예: '(주) 종근당' -> '(주)종근당')
            entp_name = item.get('entp_name', '').replace(' ', '')
            
            # 필터 조건: '종근당' 포함 AND '바이오' 미포함
            if '종근당' in entp_name and '바이오' not in entp_name:
                ckd_list.append(item)
        
        if not ckd_list:
            return f"✅ [{today}] 현재 API상에는 (주)종근당 허가 건이 없습니다. (동기화 대기 중)"

        # 메시지 생성
        message = f"🔔 [(주)종근당 신규 허가 알림]\n📅 날짜: {today}\n\n"
        for prod in ckd_list:
            message += f"✅ 제품명: {prod.get('item_name')}\n"
            message += f"🏢 업체명: {prod.get('entp_name')}\n"
            message += f"📦 구분: {prod.get('etc_otc_code')}\n"
            message += f"🔗 상세: https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail?itemSeq={prod.get('item_seq')}\n"
            message += f"------------------\n"
            
        return message

    except Exception as e:
        return f"❌ 실행 중 오류 발생: {str(e)}"

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

if __name__ == "__main__":
    # 환경변수 체크
    if not all([DATA_GO_KR_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        print("환경변수 설정이 누락되었습니다.")
        sys.exit(1)
    
    # ckd 이름으로 바뀐 함수 실행
    result_msg = get_ckd_products()
    send_telegram(result_msg)
