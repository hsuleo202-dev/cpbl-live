import requests, json, re
from datetime import datetime

# 自動偵測今天日期與賽程
now = datetime.now()
DATE_STR = now.strftime("%Y/%m/%d")
YEAR, MONTH = now.strftime("%Y"), str(int(now.strftime("%m")))
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def get_today_game():
    res = session.get(f"https://www.cpbl.com.tw/schedule/index?year={YEAR}&month={MONTH}&kindCode=A")
    matches = re.findall(rf'{DATE_STR}.*?gameSno=(\d+)', res.text, re.DOTALL)
    for sno in matches:
        if "味全" in session.get(f"https://www.cpbl.com.tw/box/index?gameSno={sno}&year={YEAR}&kindCode=A").text:
            return sno
    return None

GAME_SNO = get_today_game()
if GAME_SNO:
    res = session.get(f"https://www.cpbl.com.tw/box/index?gameSno={GAME_SNO}&year={YEAR}&kindCode=A")
    token = re.search(r'__RequestVerificationToken.*?value="(.*?)"', res.text).group(1)
    api = session.post("https://www.cpbl.com.tw/box/getlive", data={'__RequestVerificationToken': token, 'GameSno': GAME_SNO, 'KindCode': 'A', 'Year': YEAR, 'SelectYear': YEAR, 'SelectMonth': MONTH})
    data = api.json()
    
    # 完整保留所有欄位給晶片
    detail = json.loads(data["GameDetailJson"])[0]
    logs = json.loads(data["LiveLogJson"])
    latest = logs[-1] if logs else {}
    
    final_data = {
        "detail": detail,
        "latest": latest,
        "is_game_found": True
    }
    with open("cpbl.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False)
