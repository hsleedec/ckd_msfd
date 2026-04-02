import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    # 환경변수 로드
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # [날짜 조건] 지난 월요일부터 오늘까지 (최근 7일)
        now = datetime.now()
        start_date = (now - timedelta(days=7)).strftime('%Y%m%d')
        end_date = now.strftime('%Y%m%d')

        # [API 요청] 날짜 구간을 명시적으로 지정 (이게 가장 확실한 정공법)
        params = {
            'serviceKey': api_key,
            'type': 'json',
            'numOfRows': '100',
            'pageNo': '1',
            'start_prmsn_dt': start_date,
            'end_prmsn_dt': end_date
        }
        
        res = requests.get(url, params=params, timeout=30)
        items_data = res.json().get('body', {}).get('items', [])
        items = [items_data] if isinstance(items_data, dict) else items_data

        found = []
        latest_item_in_api = "없음"
        latest_date_in_api = "없음"

        if items and items[0]:
            # API가 뱉은 것 중 가장 최신 데이터 기록 (디버깅용)
            latest_item_in_api = items[0].get('item_name', '알 수 없음')
            latest_date_in_api = items[0].get('prmsn_dt', '알 수 없음')

            for i in items:
                entp_kor = str(i.get('entp_name', ''))
                entp_eng = str(i.get('entp_eng_name', '')).upper()
                item_name = str(i.get('item_name', ''))
                prmsn_dt = str(i.get('prmsn_dt', ''))

                # [교집합 필터] 한글 '종근당' 혹은 영문 'CHONG KUN DANG' 포함 시 수집
                if ('종근당' in entp_kor) or ('CHONG KUN DANG' in entp_eng):
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        # 결과 전송
        if found:
            msg = f"🚀 [주간 종근당 허가 리포트]\n기간: {start_date} ~ {end_date}\n\n" + "\n".join(sorted(list(set(found)), reverse=True))
        else:
            msg = (f"🔔 이번 주 종근당 허가 내역 없음\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"📡 API 서버 최신 데이터 현황:\n"
                   f"👉 {latest_item_in_api}\n"
                   f"📅 허가일자: {latest_date_in_api}\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"※ 위 날짜가 3/27 이전이면 식약처 API DB가 아직 업데이트 안 된 겁니다.")

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러 발생: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
