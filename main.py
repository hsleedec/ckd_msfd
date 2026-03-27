import requests
import os

def get_final_check():
    # 1. API 키 및 텔레그램 설정
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    # 2. 식약처 API 주소 (최신순으로 100개 가져오기)
    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'
    params = {
        'serviceKey': api_key,
        'type': 'json',
        'numOfRows': '100',  # 최근 허가된 100건을 통째로 긁음
        'pageNo': '1'
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        items = data.get('body', {}).get('items', [])
        
        if not items:
            msg = "⚠️ 식약처 API에서 데이터를 가져오지 못했습니다. (서버 응답 없음)"
        else:
            # 3. 검색 대상 필터링 (종근당 & 한미약품 둘 다 찾아보기)
            found_list = []
            for item in items:
                entp = item.get('entp_name', '')
                prod = item.get('item_name', '')
                date = item.get('prmsn_dt', '')
                
                # 종근당 또는 한미약품이 포함된 경우 수집
                if '종근당' in entp or '한미약품' in entp:
                    found_list.append(f"[{date}] {entp}: {prod}")

            if not found_list:
                # 테스트를 위해 최근 1번 제품 이름이라도 보내기
                first_item = items[0].get('item_name')
                msg = f"✅ 최근 100건 중 대상 업체가 없습니다.\n(최신 등록 제품: {first_item})"
            else:
                msg = "🚀 [최근 허가 알림]\n" + "\n".join(found_list)

        # 4. 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': msg})
        
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': f"❌ 에러 발생: {str(e)}"})

if __name__ == "__main__":
    get_final_check()
