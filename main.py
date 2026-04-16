import requests
import os
from datetime import datetime, timedelta
import json


def run():
    api_key = os.environ.get('DATA_GO_KR_API_KEY')

    url = "http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07"

    now = datetime.now()
    start_date = (now - timedelta(days=30)).strftime('%Y%m%d')
    end_date = now.strftime('%Y%m%d')

    params = {
        "serviceKey": api_key,
        "type": "json",
        "numOfRows": "100",
        "pageNo": "1",
        "start_prmsn_dt": start_date,
        "end_prmsn_dt": end_date
    }

    res = requests.get(url, params=params, timeout=30)
    res.raise_for_status()
    data = res.json()

    # ---------------------------
    # 1. items 추출 (구조 방어)
    # ---------------------------
    items = data.get("body", {}).get("items", [])

    if isinstance(items, dict):
        items = items.get("item", items)

    if isinstance(items, dict):
        items = [items]

    if not isinstance(items, list):
        items = []

    # ---------------------------
    # 2. 디버깅 출력 (핵심)
    # ---------------------------
    print("\n===== RAW SAMPLE (items[0]) =====")
    if items:
        print(json.dumps(items[0], indent=2, ensure_ascii=False))
    else:
        print("NO DATA")

    # ---------------------------
    # 3. CKD 필터 (확정: (주)종근당)
    # ---------------------------
    filtered = []

    for i in items:
        text = str(i)

        if "(주)종근당" not in text:
            continue

        # 날짜 후보들
        date = (
            i.get("prmsn_dt")
            or i.get("PRMSN_DT")
            or i.get("prdlst_prmsn_ymd")
            or i.get("PRDLST_PRMSN_YMD")
            or i.get("prdlstPrmsnYmd")
        )

        name = i.get("item_name") or i.get("ITEM_NAME") or "unknown"

        filtered.append({
            "name": name,
            "date": date
        })

    # ---------------------------
    # 4. 결과 확인
    # ---------------------------
    print("\n===== FILTERED =====")
    print(filtered[:5])

    # ---------------------------
    # 5. 정렬
    # ---------------------------
    filtered = [x for x in filtered if x["date"]]

    filtered.sort(key=lambda x: x["date"], reverse=True)

    latest = filtered[:5]

    # ---------------------------
    # 6. 출력
    # ---------------------------
    print("\n===== LATEST =====")
    for x in latest:
        print(x)


if __name__ == "__main__":
    run()
