import requests
import os
from datetime import datetime, timedelta

def check_pharm_approvals():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    
    try:
        # [조건 4] 날짜 계산: 오늘부터 7일 전까지 (형식: 20260325)
        today = datetime.today()
        start_date = (today - timedelta(days=7)).strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')

        # [조건 2] 최신순 소팅을 위해 API에 날짜 범위를 직접 지정하여 요청
        # 한 번에 100건씩 가져오며, 최근 일주일 데이터가 100건을 넘을 수 있으므로 반복 확인
        found = []
        
        # 안전하게 최근 데이터 300건(3페이지)을 훑습니다.
        for page in range(1, 4):
            params = {
                'serviceKey': api_key,
                'type': 'json',
                'numOfRows': '100',
                'pageNo': str(page),
                'start_prmsn_dt': start_date, # 시작일
                'end_prmsn_dt': end_date      # 종료일
            }
            
            res = requests.get(url, params=params, timeout=30)
            data = res.json()
            items_raw = data.get('body', {}).get('items', [])
            items = [items_raw] if isinstance(items_raw, dict) else items_raw

            if not items:
                break # 더 이상 데이터가 없으면 중단

            for i in items:
                # [조건 1] 업체명(한글/영문) 교집합 체크
                entp_kor = str(i.get('entp_name', ''))
                entp_eng = str(i.get('entp_eng_name', '')).upper()
                item_name = str(i.get('item_name', ''))
                prmsn_dt = str(i.get('prmsn_dt', ''))

                # 종근당 또는 CHONG KUN DANG 키워드 검사
                if ('종근당' in entp_kor) or ('CHONG KUN DANG' in entp_eng):
                    found.append(f"✅ {item_name} ({prmsn_dt})")

        # [조건 3] 교집합 결과 처리 및 전송
        if found:
            # 중복 제거 및 최신순 정렬
            final_list = sorted(list(set(found)), reverse=True)
            msg = f"🚀 [종근당 신규 허가 확인]\n검색범위: {start_date} ~ {end_date}\n\n" + "\n".join(final_list)
        else:
            # 작동 확인을 위한 샘플 출력 (가장 최근에 허가된 타사 제품 하나 노출)
            sample = items[0] if items else {}
            s_name = sample.get('item_name', '없음')
            s_dt = sample.get('prmsn_dt', '없음')
            msg = (f"🔔 최근 1주일 종근당 내역 없음\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"📡 API 응답 확인(최신순):\n"
                   f"👉 {s_name}\n"
                   f"📅 허가일자: {s_dt}\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"※ 이 날짜가 3월 27일 근처면 서버는 정상이나 데이터가 아직 안 온 겁니다.")

        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': f"❌ 시스템 오류: {str(e)}"})

if __name__ == "__main__":
    check_pharm_approvals()
