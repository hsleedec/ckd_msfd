import requests
import os
from datetime import datetime, timedelta


def extract_date(item):
    """
    날짜 필드 자동 탐색 (공공데이터 구조 변형 대응)
    """
    possible_keys = [
        'prmsn_dt',
        'PRMSN_DT',
        'prdlst_prmsn_ymd',
        'PRDLST_PRMSN_YMD',
        'prdlstPrmsnYmd',
        'item_prmsn_dt',
        'permit_dt',
        'PERMIT_DT'
    ]

    for k in possible_keys:
        v = item.get(k)
        if v:
            return v

    return None


def check_chongkundang_latest():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'

    try:
        # 1. 기간 설정 (최근 30일)
        now = datetime.now()
        start_date = (now - timedelta(days=30)).strftime('%Y%m%d')
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
        res.raise_for_status()
        data = res.json()

        # 2. items 구조 방어 처리
        items = data.get('body', {}).get('items', [])

        if isinstance(items, dict):
            items = items.get('item', items)

        if isinstance(items, dict):
            items = [items]

        if not isinstance(items, list):
            items = []

        filtered = []

        # 3. CKD 필터 + 날짜 추출
        for i in items:
            raw = str(i).upper()

            if ('종근당' in raw) or ('CHONG KUN DANG' in raw) or ('CKD' in raw):

                date = extract_date(i)
                name = i.get('item_name') or i.get('ITEM_NAME') or 'unknown'

                filtered.append({
                    'name': name,
                    'date': date
                })

        # 4. 날짜 없는 데이터 제거
        filtered = [x for x in filtered if x['date']]

        # 5. 최신순 정렬 (핵심)
        filtered.sort(key=lambda x: x['date'], reverse=True)

        latest = filtered[:5]

        # 6. 메시지 생성
        if latest:
            msg = "🚀 종근당 최신 허가 TOP\n"
            msg += f"기간: {start_date} ~ {end_date}\n\n"

            for x in latest:
                msg += f"✔ {x['name']} ({x['date']})\n"

        else:
            msg = (
                "🔔 종근당 데이터 없음\n"
                f"조회기간: {start_date} ~ {end_date}\n"
                "※ 필터 조건 또는 API 구조 확인 필요"
            )

        # 7. 텔레그램 전송
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                'chat_id': chat_id,
                'text': msg
            }
        )

    except Exception as e:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                'chat_id': chat_id,
                'text': f"❌ 에러 발생: {str(e)}"
            }
        )


if __name__ == "__main__":
    check_chongkundang_latest()
