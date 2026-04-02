import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # [날짜 조건] 오늘부터 6개월(180일) 전까지로 대폭 확대
        now = datetime.now()
        start_date = (now - timedelta(days=180)).strftime('%Y%m%d')
        end_date = now.strftime('%Y%m%d')

        found = []
        # 최근 6개월 데이터가 많을 수 있으므로 1~5페이지(총 500건)까지 전수조사
        for page in range(1, 6):
            params = {
                'serviceKey': api_key,
                'type': 'json',
                'numOfRows': '100',
                'pageNo': str(page),
                'start_prmsn_dt': start_date,
                'end_prmsn_dt': end_date
            }
            
            res = requests.get(url, params=params, timeout=30)
            items_raw = res.json().get('body', {}).get('items', [])
            items = [items_raw] if isinstance(items_raw, dict) else items_raw

            if not items or not items[0]:
                break # 더 이상 데이터가 없으면 중단

            for i in items:
                entp_kor = str(i.get('entp_name', ''))
                entp_eng = str(i.get('entp_eng_name', '')).upper()
                item_name = str(i.get('item_name', ''))
                prmsn_dt = str(i.get('prmsn_dt', ''))

                # 종근당 또는 CHONG KUN DANG 포함 여부 확인
                if ('종근당' in entp_kor) or ('CHONG KUN DANG' in entp_eng):
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        # 결과 전송
        if found:
            # 중복 제거 및 날짜 최신순 정렬
            final_list = sorted(list(set(found)), reverse=True)
            msg = f"🚀 [종근당 6개월 허가 리포트]\n조회범위: {start_date} ~ {end_date}\n\n" + "\n".join(final_list)
        else:
            msg = f"🔔 최근 6개월간 종근당 허가 내역이 API상에 없습니다.\n(조회범위: {start_date} ~ {end_date})"

        # 메시지가 너무 길면 텔레그램에서 잘릴 수 있으니 4000자 단위로 끊어서 전송 가능성 대비
        if len(msg) > 4000:
            msg = msg[:3900] + "\n... (이하 생략)"

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러 발생: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
