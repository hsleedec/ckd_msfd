import requests
import os

def check_pharm_approvals():
    # 1. GitHub Secrets에서 환경변수 가져오기
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    # 2. 식약처 API 주소 및 파라미터 (최신 100건 조회)
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'numOfRows': '100', 
        'pageNo': '1'
    }

    try:
        # API 호출
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
        items = data.get('body', {}).get('items', [])
        
        if isinstance(items, dict): # 결과가 1건일 경우 예외처리
            items = [items]

        found = []
        if items:
            for i in items:
                entp = i.get('entp_name', '')
                item_name = i.get('item_name', '')
                prmsn_dt = i.get('prmsn_dt', '')
                
                # [검증 로직] 종근당과 한미약품을 모두 찾습니다.
                if '종근당' in entp or '한미약품' in entp:
                    found.append(f"✅ {entp}: {item_name} ({prmsn_dt})")

        # 3. 메시지 구성
        if found:
            # 최신순 정렬 및 중복 제거
            found = sorted(list(set(found)), reverse=True)
            msg = "🚀 [제약사 신규 허가 감지!]\n\n" + "\n".join(found)
        else:
            # 아무것도 없을 때 API 서버 상태 확인용 데이터 추출
            latest_item = items[0].get('item_name', '알수없음') if items else "데이터없음"
            latest_date = items[0].get('prmsn_dt', '날짜없음') if items else "날짜없음"
            
            msg = (f"🔔 아직 종근당/한미 데이터가 API에 없습니다.\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"📦 API 서버 최신 등록 제품:\n"
                   f"👉 {latest_item}\n"
                   f"📅 허가일자: {latest_date}\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"※ 이 날짜가 3월 27일 이전이면 식약처 API가 아직 업데이트 안 된 것입니다.")

        # 4. 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': msg})
        
    except Exception as e:
        error_msg = f"❌ 시스템 에러 발생: {str(e)}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': error_msg})
