import requests
import json

GAME_SNO = "163"
YEAR = "2026"
MONTH = "6"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
})

index_url = f"https://www.cpbl.com.tw/box/index?gameSno={GAME_SNO}&year={YEAR}&kindCode=A"
response_index = session.get(index_url)

if response_index.status_code == 200:
    try:
        token_start = response_index.text.find('__RequestVerificationToken" type="hidden" value="') + 49
        token_end = response_index.text.find('"', token_start)
        fresh_token = response_index.text[token_start:token_end]
    except Exception:
        print("❌ 提取 Token 失敗")
        exit()

    api_url = "https://www.cpbl.com.tw/box/getlive"
    payload = {
        '__RequestVerificationToken': fresh_token,
        'GameSno': GAME_SNO,
        'KindCode': 'A',
        'Year': YEAR,
        'PrevOrNext': '0',
        'SelectKindCode': 'A',
        'SelectYear': YEAR,
        'SelectMonth': MONTH
    }

    response_api = session.post(api_url, data=payload)

    if response_api.status_code == 200:
        raw_json = response_api.json()
        with open("cpbl.json", "w", encoding="utf-8") as f:
            json.dump(raw_json, f, ensure_ascii=False, indent=4)
        print("🎉 成功寫入 cpbl.json")
