import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # 1. 날짜 설정: 최근 7일 (4월 16일 기준 4월 9일까지)
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
        res_json = res.json()
        
        # 데이터 바구니 추출
        items_data = res_json.get('body', {}).get('items', [])
        items = [items_data] if isinstance(items_data, dict) else items_data

        if not items or not items[0]:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          data={'chat_id': chat_id, 'text': "🔔 해당 기간에 데이터가 아예 없습니다."})
            return

        # [핵심 1] 날짜 필드(prmsn_dt)를 기준으로 '직접' 최신순 정렬
        # 데이터에 날짜가 없으면 가장 옛날 날짜로 취급해서 뒤로 보냄
        items.sort(key=lambda x: str(x.get('prmsn_dt', '0000-00-00')).replace('-', ''), reverse=True)

        found = []
        for i in items:
            # [핵심 2] 이름표(Key) 대소문자 방어
            item_name = i.get('item_name') or i.get('ITEM_NAME') or "제품명 확인불가"
            prmsn_dt = i.get('prmsn_dt') or i.get('PRMSN_DT') or "날짜 확인불가"
            
            # 전체 텍스트에서 '종근당' 키워드 수색
            raw_str = str(i).upper()
            if ('종근당' in raw_str) or ('CHONG KUN DANG' in raw_str) or ('CKD' in raw_str):
                found.append(f"✅ {item_name} | {prmsn_dt}")

        # 3. 결과 보고
        if found:
            # 최신순으로 정렬된 상태에서 상위 노출
            msg = f"🚀 [종근당 최신 허가 내역]\n기간: {start_date} ~ {end_date}\n\n" + "\n".join(found)
        else:
            # 디버깅용: 종근당은 없더라도 API가 준 가장 최신 제품 1개 노출
            best_sample = items[0]
            s_name = best_sample.get('item_name') or best_sample.get('ITEM_NAME') or "이름모름"
            s_dt = best_sample.get('prmsn_dt') or best_sample.get('PRMSN_DT') or "날짜모름"
            msg = (f"🔔 최근 1주일 종근당 내역 없음\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"📡 [현재 API 최신 데이터]\n"
                   f"👉 {s_name}\n"
                   f"📅 허가일자: {s_dt}\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"※ 이 날짜가 오늘 날짜와 가까우면 로직은 완벽한 겁니다.")

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 시스템 오류: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
