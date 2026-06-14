import requests
import json
from datetime import datetime
import re

# 1. 自動偵測今天日期
now = datetime.now()
DATE_STR = now.strftime("%Y/%m/%d") # 格式如 2026/06/14
YEAR = now.strftime("%Y")
MONTH = str(int(now.strftime("%m")))

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})

# 2. 自動找尋今天味全龍的比賽場次
def get_today_game_sno():
    url = f"https://www.cpbl.com.tw/schedule/index?year={YEAR}&month={MONTH}&kindCode=A"
    res = session.get(url)
    
    # 用正則表達式找出今天日期的所有場次
    # 邏輯：先找到日期，再找出該日期下的 gameSno
    pattern = rf'{DATE_STR}.*?gameSno=(\d+)'
    matches = re.findall(pattern, res.text, re.DOTALL)
    
    for sno in matches:
        # 檢查該場次是否有味全
        box_url = f"https://www.cpbl.com.tw/box/index?gameSno={sno}&year={YEAR}&kindCode=A"
        box_res = session.get(box_url)
        if "味全" in box_res.text:
            return sno
    return None

GAME_SNO = get_today_game_sno()

if not GAME_SNO:
    print("💤 今天沒有味全龍的比賽，收工。")
    exit()

# 3. 抓取比分資料
index_url = f"https://www.cpbl.com.tw/box/index?gameSno={GAME_SNO}&year={YEAR}&kindCode=A"
res = session.get(index_url)
token = re.search(r'__RequestVerificationToken.*?value="(.*?)"', res.text).group(1)

api_url = "https://www.cpbl.com.tw/box/getlive"
payload = {
    '__RequestVerificationToken': token,
    'GameSno': GAME_SNO, 'KindCode': 'A', 'Year': YEAR,
    'PrevOrNext': '0', 'SelectKindCode': 'A', 'SelectYear': YEAR, 'SelectMonth': MONTH
}
res_api = session.post(api_url, data=payload)

if res_api.status_code == 200:
    data = res_api.json()
    if data.get("Success"):
        # 整理成晶片專用的精簡格式
        detail = json.loads(data["GameDetailJson"])[0]
        logs = json.loads(data["LiveLogJson"])
        latest = logs[-1] if logs else {}
        
        final_data = {
            "custom_info": {"game_sno": GAME_SNO, "date": DATE_STR},
            "GameDetail": {
                "v_team": detail.get("VisitingTeamName"),
                "h_team": detail.get("HomeTeamName"),
                "v_score": detail.get("VisitingTotalScore", 0),
                "h_score": detail.get("HomeTotalScore", 0)
            },
            "LiveStatus": {
                "balls": int(float(latest.get("BallCnt", 0))),
                "strikes": int(float(latest.get("StrikeCnt", 0))),
                "outs": int(float(latest.get("OutCnt", 0)))
            }
        }
        with open("cpbl.json", "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False)
        print(f"✅ 成功更新味全賽事: {GAME_SNO}")
