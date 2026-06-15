import requests
import json
import re
import sys
import time

# ====================================================================
# 🎯 雲端設定與偽裝 Header
# ====================================================================
GAS_URL = "https://script.googleusercontent.com/macros/echo?user_content_key=AUkAhnSMHjH8kwbduHPEN2Tgi2DVWCQWG_KGQYYPbRqlVahxG5xAGMnGu_XFdhOU8aVyvqzdcLFoh8ihbGRVkkTuFaw5v2BtXH_Uj3Z_IjiyQlQ3Q61I22cZR0uXqoaM2m7cWPXPc6Z0oYwg7uHbdAFbkYkx-iw2_Kj-N6c3ANFAkyPsyvL4SraM9bIf_cQL3pZfv1ocWrJ5ilBU1CI3M0FUnDGohdEksu9FxAGd7faLzR2fb_xWSJoUgbo46EFmpmNnzP9s0KMJpqSddIN-FYCBuwlfAwKBag&lib=M2LHac6VRrvq7A3NOANO4ZYtiO8R5qc0s"

session = requests.Session()
# 模擬真實瀏覽器行為，包含 Accept 語系與完整的安全 Header
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Referer': 'https://www.cpbl.com.tw/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
})

print("🔄 正在從 Google Apps Script 獲取場次資訊...")
try:
    gas_res = session.get(GAS_URL, timeout=15)
    gas_res.raise_for_status()
    gas_data = gas_res.json()
    
    GAME_SNO = str(gas_data["game_sno"])
    GAS_DATE = gas_data["date"]
    YEAR = GAS_DATE.split('/')[0]
    MONTH = str(int(GAS_DATE.split('/')[1]))
    
    print(f"📌 同步成功！場號: {GAME_SNO} | 日期: {GAS_DATE}")
except Exception as e:
    print(f"❌ 【雲端錯誤】: {e}")
    sys.exit(1)

# ====================================================================
# 🚀 獲取 Token (增加延遲以模擬人類讀取速度)
# ====================================================================
index_url = f"https://www.cpbl.com.tw/box/index?gameSno={GAME_SNO}&year={YEAR}&kindCode=A"
print("🔄 請求官網 Token 中...")

try:
    # 建立 Session 時先請求一次首頁獲取 Cookie
    session.get("https://www.cpbl.com.tw/", timeout=15)
    time.sleep(1) # 增加延遲避免 403
    
    response_index = session.get(index_url, timeout=15)
    if response_index.status_code == 403:
        print("❌ 【403 錯誤】伺服器拒絕訪問，爬蟲節點 IP 可能被列管。")
        sys.exit(1)
        
    token_match = re.search(r'__RequestVerificationToken"\s+type="hidden"\s+value="(.*?)"', response_index.text)
    if token_match:
        fresh_token = token_match.group(1)
    else:
        print("❌ 【結構錯誤】找不到 Token")
        sys.exit(1)
except Exception as e:
    print(f"❌ 【異常】: {e}")
    sys.exit(1)

# ====================================================================
# 🚀 發送 Post 請求
# ====================================================================
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

print("🚀 正在對 Live API 發送請求...")
try:
    response_api = session.post(api_url, data=payload, timeout=15)
    if response_api.status_code == 200:
        raw_json = response_api.json()
        if raw_json.get("Success"):
            # 解析邏輯
            game_detail = json.loads(raw_json.get("GameDetailJson", "[]"))
            scoreboard = {}
            for item in game_detail:
                if int(float(item.get("GameSno", 0))) == int(float(GAME_SNO)):
                    scoreboard = {
                        "客隊": item.get("VisitingTeamName"),
                        "客隊分數": int(float(item.get("VisitingTotalScore", 0))),
                        "主隊": item.get("HomeTeamName"),
                        "主隊分數": int(float(item.get("HomeTotalScore", 0))),
                        "狀態": item.get("GameStatusChi")
                    }
                    break
            
            live_logs = json.loads(raw_json.get("LiveLogJson", "[]"))
            balls = strikes = outs = 0
            if live_logs:
                latest = live_logs[-1]
                balls = int(float(latest.get("BallCnt", 0)))
                strikes = int(float(latest.get("StrikeCnt", 0)))
                outs = int(float(latest.get("OutCnt", 0)))
            
            final_data = {
                "game_sno": int(GAME_SNO),
                "v_team": scoreboard.get("客隊"),
                "h_team": scoreboard.get("主隊"),
                "v_score": scoreboard.get("客隊分數"),
                "h_score": scoreboard.get("主隊分數"),
                "balls": balls,
                "strikes": strikes,
                "outs": outs,
                "status": scoreboard.get("狀態")
            }
            
            with open("cpbl.json", "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            print("🎉 數據已成功存入 cpbl.json！")
        else:
            print("❌ 【API 錯誤】Success 為 False")
            sys.exit(1)
    else:
        print(f"❌ 【API 請求失敗】狀態碼: {response_api.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ 【錯誤】: {e}")
    sys.exit(1)
