import requests
import json
import os

# 1. 讀取晶片傳來的設定檔
def load_config():
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                return json.load(f).get("game_sno", "163")
    except:
        pass
    return "163" # 預設場次

GAME_SNO = load_config()
YEAR = "2026"
MONTH = "6"

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})

# 2. 爬取中職資料
def fetch_data():
    index_url = f"https://www.cpbl.com.tw/box/index?gameSno={GAME_SNO}&year={YEAR}&kindCode=A"
    res = session.get(index_url)
    if res.status_code != 200: return None

    # 提取 Token
    token_start = res.text.find('__RequestVerificationToken" type="hidden" value="') + 49
    token = res.text[token_start:res.text.find('"', token_start)]

    api_url = "https://www.cpbl.com.tw/box/getlive"
    payload = {
        '__RequestVerificationToken': token,
        'GameSno': GAME_SNO, 'KindCode': 'A', 'Year': YEAR,
        'PrevOrNext': '0', 'SelectKindCode': 'A', 'SelectYear': YEAR, 'SelectMonth': MONTH
    }
    
    res_api = session.post(api_url, data=payload)
    if res_api.status_code == 200:
        return res_api.json()
    return None

# 3. 處理數據並產出極簡 JSON
raw_data = fetch_data()
if raw_data and raw_data.get("Success"):
    game_detail = json.loads(raw_data.get("GameDetailJson", "[]"))
    live_logs = json.loads(raw_data.get("LiveLogJson", "[]"))
    
    # 找當前場次數據
    game = next((item for item in game_detail if str(item.get("GameSno")) == GAME_SNO), {})
    latest = live_logs[-1] if live_logs else {}

    # 組裝給晶片的「懶人包」
    final_data = {
        "custom_info": {"game_sno": GAME_SNO, "date": "2026/06/14"},
        "Success": True,
        "GameDetail": {
            "v_team": game.get("VisitingTeamName"),
            "h_team": game.get("HomeTeamName"),
            "v_score": game.get("VisitingTotalScore", 0),
            "h_score": game.get("HomeTotalScore", 0)
        },
        "LiveStatus": {
            "inning": latest.get("InningChi"),
            "balls": int(float(latest.get("BallCnt", 0))),
            "strikes": int(float(latest.get("StrikeCnt", 0))),
            "outs": int(float(latest.get("OutCnt", 0))),
            "base": [bool(latest.get("FirstBase")), bool(latest.get("SecondBase")), bool(latest.get("ThirdBase"))]
        }
    }

    with open("cpbl.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False)
    print(f"✅ 成功更新場次 {GAME_SNO}")
else:
    print("❌ 爬取失敗")
