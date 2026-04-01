import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # 1. 전체 개수 확인 후 마지막 구역 계산
        count_res = requests.get(url, params={'serviceKey': api_key, 'type': 'json', 'numOfRows': '1'}, timeout=30)
        total_count = count_res.json().get('body', {}).get('totalCount', 45000)
        last_page = (total_count // 100) + 1  # 페이지 번호 수정: +1을 해야 전체 페이지 수가 맞음
        
        found = []
        limit_date = (datetime.today() - timedelta(days=7)).strftime('%Y%m%d')  # 최근 7일 날짜

        # 2. 마지막 300건을 샅샅이 뒤집습니다.
        for page in range(last_page - 1, last_page + 2):
            if page < 1: continue
            params = {'serviceKey': api_key, 'type': 'json', 'numOfRows': '100', 'pageNo': str(page)}
            res = requests.get(url, params=params, timeout=30)
            items_data = res.json().get('body', {}).get('items', [])
            items = [items_data] if isinstance(items_data, dict) else items_data

            if items:
                for i in items:
                    # [필터링 핵심] 한글/영문 가리지 않고 종근당 키워드만 있으면 수집
                    entp_kor = str(i.get('entp_name', ''))
                    entp_eng = str(i.get('entp_name_eng', '')).upper()  # 필드명이 정확한지 확인 필요
                    item_name = str(i.get('item_name', ''))
                    raw_dt = str(i.get('prmsn_dt', '')).replace('-', '')  # 날짜 형식 처리

                    # 영문명 'CHONG KUN DANG'이 포함되어 있는지 확인 (대문자 처리)
                    if ('종근당' in entp_kor or 'CHONG KUN DANG' in entp_eng) and raw_dt >= limit_date:
                        found.append(f"✅ {item_name} / {raw_dt}")

        # 3. 결과 메시지 구성 (스크린샷의 데이터가 나오도록 최적화)
        if found:
            # 중복 제거 및 최신순 정렬
            final_list = sorted(list(set(found)), reverse=True)
            msg = f"🚀 [종근당 신규 허가 알림]\n\n" + "\n".join(final_list)
        else:
            msg = f"🔔 최근 1주일 종근당 내역 없음\n(식약처 API DB 동기화 대기 중...)"

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 시스템 에러: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
