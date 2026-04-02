import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # 1. 날짜 설정: 최근 7일 (4월 2일 기준 3월 26일까지 커버)
        now = datetime.now()
        start_date = (now - timedelta(days=7)).strftime('%Y%m%d')
        end_date = now.strftime('%Y%m%d')

        params = {
            'serviceKey': api_key,
            'type': 'json',
            'numOfRows': '100',
            'pageNo': '1',
            'start_prmsn_dt': start_date,
            'end_prmsn_dt': end_date
        }
        
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()  # 상태 코드 확인
        res_json = res.json()
        
        # 데이터가 들어있는 바구니(items) 찾기
        items_data = res_json.get('body', {}).get('items', [])
        items = [items_data] if isinstance(items_data, dict) else items_data

        found = []
        
        if items and items[0]:
            for i in items:
                # [개선] 대문자/소문자 상관없이 제품명과 날짜를 추출
                # 식약처 API가 대소문자를 섞어 써도 다 잡아냅니다.
                item_name = i.get('item_name') or i.get('ITEM_NAME') or "이름모를약"
                prmsn_dt = i.get('prmsn_dt') or i.get('PRMSN_DT') or "날짜모름"
                
                # 데이터 전체를 글자로 바꿔서 '종근당' 키워드 수색
                raw_str = str(i).upper()
                if ('종근당' in raw_str) or ('CHONG KUN DANG' in raw_str) or ('CKD' in raw_str):
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        # 3. 결과 보고
        if found:
            msg = f"🚀 [종근당 신규 허가 확인]\n({start_date}~{end_date})\n\n" + "\n".join(sorted(list(set(found)), reverse=True))
        else:
            # [필살기] 내역이 없으면, 아예 API가 보내준 '날것의 데이터'를 그대로 텔레그램에 쏩니다.
            # 이걸 보면 왜 안 낚이는지 제가 100% 잡아낼 수 있습니다.
            sample_raw = str(items[0]) if items else "데이터 없음"
            msg = (f"🔔 이번 주 종근당 내역 없음\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"📡 [API 실제 응답 데이터 1건]\n"
                   f"{sample_raw[:200]}\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"※ 이 글자들 사이에 '종근당'이 없으면 API 서버가 범인입니다.")

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 에러 발생: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
