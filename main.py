import requests
import os
from datetime import datetime, timedelta


def check_chongkundang_latest():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    url = 'http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07'

    try:
        # 1. 최근 30일 범위
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

        items = data.get('body', {}).get('items', [])
        if isinstance(items, dict):
            items = [items]

        filtered = []

        # 2. 종근당 필터링
        for i in items:
            raw = str(i).upper()

            if ('종근당' in raw) or ('CHONG KUN DANG' in raw) or ('CKD' in raw):
                item_name = i.get('item_name') or i.get('ITEM_NAME', '이름없음')
                prmsn_dt = i.get('prmsn_dt') or i.get('PRMSN_DT', '00000000')

                filtered.append({
                    "name": item_name,
                    "date": prmsn_dt
                })

        # 3. 허가일 기준 최신순 정렬
        filtered = sorted(filtered, key=lambda x: x['date'], reverse=True)

        latest = filtered[:5]  # 최신 5건

        # 4. 메시지 생성
        if latest:
            msg_lines = [
                "🚀 종근당 최신 허가 TOP",
                f"기간: {start_date} ~ {end_date}",
                ""
            ]

            for x in latest:
                msg_lines.append(f"✔ {x['name']} ({x['date']})")

            msg = "\n".join(msg_lines)

        else:
            msg = (
                "🔔 종근당 최근 허가 없음\n"
                f"조회기간: {start_date} ~ {end_date}\n"
                "※ API 응답에는 종근당 데이터가 없음"
            )

        # 5. 텔레그램 전송
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
