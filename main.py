import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # 1. 날짜 설정: 최근 7일 (낭낭하게 1주일)
        now = datetime.now()
        start_date = (now - timedelta(days=7)).strftime('%Y%m%d')
        end_date = now.strftime('%Y%m%d')

        found = []
        
        # 2. 최신 데이터 1페이지(100건) 요청
        # (날짜 구간을 지정했으므로 1페이지 100건 안에 1주일치 데이터는 다 들어옵니다)
        params = {
            'serviceKey': api_key,
            'type': 'json',
            'numOfRows': '100',
            'pageNo': '1',
            'start_prmsn_dt': start_date,
            'end_prmsn_dt': end_date
        }
        
        res = requests.get(url, params=params, timeout=30)
        res_json = res.json()
        
        # API 응답 구조가 가끔 바뀔 때를 대비해 안전하게 items 추출
        body = res_json.get('body', {})
        items_data = body.get('items', [])
        items = [items_data] if isinstance(items_data, dict) else items_data

        if items and items[0]:
            for i in items:
                # [핵심] 필드명을 따지지 않고 전체 데이터를 문자열로 변환 (전수 조사)
                raw_data_string = str(i).upper()
                item_name = i.get('item_name', '제품명 미확인')
                prmsn_dt = i.get('prmsn_dt', '날짜 미확인')

                # '종근당' 관련 키워드가 하나라도 걸리면 낚시 성공
                if ('종근당' in raw_data_string) or ('CHONG KUN DANG' in raw_data_string) or ('CKD' in raw_data_string):
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        # 3. 결과 보고
        if found:
            # 중복 제거 및 정렬
            msg = f"🚀 [종근당 신규 허가 확인]\n기간: {start_date} ~ {end_date}\n\n" + "\n".join(sorted(list(set(found)), reverse=True))
        else:
            # 여전히 실패 시, API가 도대체 뭘 보내주고 있는지 '현장 생중계'
            sample_item = items[0] if items else "응답 데이터 없음"
            msg = (f"🔔 최근 1주일 종근당 내역 없음\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"📡 [API 실시간 응답 샘플]\n"
                   f"👉 {str(sample_item)[:100]}...\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"※ 이 샘플에도 데이터가 없으면 식약처 서버가 텅 빈 겁니다.")

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러 상세: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
