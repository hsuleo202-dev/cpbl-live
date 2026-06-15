import requests
import json
import re
import sys
import time
import random

# ====================================================================
# 🎯 雲端設定區
# ====================================================================
GAS_URL = "https://script.googleusercontent.com/macros/echo?user_content_key=AUkAhnSMHjH8kwbduHPEN2Tgi2DVWCQWG_KGQYYPbRqlVahxG5xAGMnGu_XFdhOU8aVyvqzdcLFoh8ihbGRVkkTuFaw5v2BtXH_Uj3Z_IjiyQlQ3Q61I22cZR0uXqoaM2m7cWPXPc6Z0oYwg7uHbdAFbkYkx-iw2_Kj-N6c3ANFAkyPsyvL4SraM9bIf_cQL3pZfv1ocWrJ5ilBU1CI3M0FUnDGohdEksu9FxAGd7faLzR2fb_xWSJoUgbo46EFmpmNnzP9s0KMJpqSddIN-FYCBuwlfAwKBag&lib=M2LHac6VRrvq7A3NOANO4ZYtiO8R5qc0s"

session = requests.Session()
# 強化的偽裝 Header
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Referer': 'https://www.cpbl.com.tw/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Connection': 'keep-alive'
})

def fetch_with_defense(url, is_post=False, payload=None):
    """帶有防禦機制的請求函數"""
    for i in range(3): # 嘗試 3 次
        try:
            if is_post: res = session.post(url, data=payload, timeout=20)
            else: res = session.get(url, timeout=20)
            
            if res.status_code == 200: return res
            
            # 如果觸發 403，變更 UA 並冷卻 10 秒
            if res.status_code == 403:
                session.headers.update({'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'})
                time.sleep(10)
        except:
            time.sleep(5)
    return None

# ====================================================================
# 🚀 執行流程 (全程自動化)
# ====================================================================
print("🔄 自動化程序啟動...")

# 1. 從 GAS 同步目標
gas_res = fetch_with_defense(GAS_URL)
if not gas_res: sys.exit(1)
data = gas_res.json()
GAME_SNO, GAS_DATE = str(data["game_sno"]), data["date"]
YEAR, MONTH = GAS_DATE.split('/')[0], str(int(GAS_DATE.split('/')[1]))

# 2. 獲取 Token
index_url = f"https://www.cpbl.com.tw/box/index?gameSno={GAME_SNO}&year={YEAR}&kindCode=A"
idx_res = fetch_with_defense(index_url)
if not idx_res: sys.exit(1)
token = re.search(r'__RequestVerificationToken"\s+type="hidden"\s+value="(.*?)"', idx_res.text).group(1)

# 3. 發送 API 請求並清洗
api_url = "https://www.cpbl.com.tw/box/getlive"
payload = {'__RequestVerificationToken': token, 'GameSno': GAME_SNO, 'KindCode': 'A', 'Year': YEAR, 'SelectMonth': MONTH}
api_res = fetch_with_defense(api_url, True, payload)

if api_res and api_res.json().get("Success"):
    raw = api_res.json()
    game_detail = json.loads(raw.get("GameDetailJson", "[]"))
    scoreboard = next((item for item in game_detail if int(float(item.get("GameSno", 0))) == int(float(GAME_SNO))), {})
    
    live_logs = json.loads(raw.get("LiveLogJson", "[]"))
    latest = live_logs[-1] if live_logs else {}
    
    final_data = {
        "game_sno": int(GAME_SNO),
        "v_team": scoreboard.get("VisitingTeamName"),
        "h_team": scoreboard.get("HomeTeamName"),
        "v_score": int(float(scoreboard.get("VisitingTotalScore", 0))),
        "h_score": int(float(scoreboard.get("HomeTotalScore", 0))),
        "balls": int(float(latest.get("BallCnt", 0))),
        "strikes": int(float(latest.get("StrikeCnt", 0))),
        "outs": int(float(latest.get("OutCnt", 0))),
        "status": scoreboard.get("GameStatusChi")
    }
    
    with open("cpbl.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print("🎉 自動化更新成功！")
else:
    sys.exit(1)
