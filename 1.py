import requests
import json
import re
import sys

# ====================================================================
# 🎯 雲端設定區（已加入完整偽裝 Header 以避開 Google 500 錯誤）
# ====================================================================
GAS_URL = "https://script.googleusercontent.com/macros/echo?user_content_key=AUkAhnSMHjH8kwbduHPEN2Tgi2DVWCQWG_KGQYYPbRqlVahxG5xAGMnGu_XFdhOU8aVyvqzdcLFoh8ihbGRVkkTuFaw5v2BtXH_Uj3Z_IjiyQlQ3Q61I22cZR0uXqoaM2m7cWPXPc6Z0oYwg7uHbdAFbkYkx-iw2_Kj-N6c3ANFAkyPsyvL4SraM9bIf_cQL3pZfv1ocWrJ5ilBU1CI3M0FUnDGohdEksu9FxAGd7faLzR2fb_xWSJoUgbo46EFmpmNnzP9s0KMJpqSddIN-FYCBuwlfAwKBag&lib=M2LHac6VRrvq7A3NOANO4ZYtiO8R5qc0s"

session = requests.Session()
# 強化 Header 偽裝：加入 Referer 與多語言設定，讓 Google 伺服器判定為正常瀏覽器請求
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.google.com/',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'X-Requested-With': 'XMLHttpRequest'
})

print("🔄 正在從 Google Apps Script 獲取 Wemos 鎖定的目標場次與自動日期...")
try:
    gas_res = session.get(GAS_URL, timeout=15) # 增加超時上限
    gas_res.raise_for_status() 
    gas_data = gas_res.json()
    
    if "game_sno" not in gas_data or "date" not in gas_data:
        raise ValueError("GAS 回傳的 JSON 欄位不完整！")
        
    GAME_SNO = str(gas_data["game_sno"])
    GAS_DATE = gas_data["date"]
    
    date_parts = GAS_DATE.split('/')
    YEAR = date_parts[0]
    MONTH = str(int(date_parts[1]))
    
    print(f"📌 成功同步！目標場號: {GAME_SNO} | 賽事日期: {GAS_DATE} (年度:{YEAR}, 月份:{MONTH})")
except Exception as e:
    print(f"❌ 【核心錯誤】從 GAS 獲取資料失敗: {e}")
    print("🚨 程式已中斷執行，請檢查 GAS 部署網址、權限設定或網路連線。")
    sys.exit(1)

# ====================================================================
# 🚀 開始執行 CPBL 官網 Token 擷取與賽況 POST 請求
# ====================================================================
index_url = f"https://www.cpbl.com.tw/box/index?gameSno={GAME_SNO}&year={YEAR}&kindCode=A"
print(f"🔄 正在自動獲取第 {GAME_SNO} 場比賽的動態安全驗證 Token...")

try:
    response_index = session.get(index_url, timeout=15)
    if response_index.status_code == 200:
        token_match = re.search(r'__RequestVerificationToken"\s+type="hidden"\s+value="(.*?)"', response_index.text)
        if token_match:
            fresh_token = token_match.group(1)
        else:
            print("❌ 【結構錯誤】提取 Token 失敗，中職官網網頁結構可能已被微調。")
            sys.exit(1)
    else:
        print(f"❌ 【連線錯誤】無法連線至 CPBL 官網 Box 首頁 (狀態碼: {response_index.status_code})")
        sys.exit(1)
except Exception as e:
    print(f"❌ 【連線異常】連線 CPBL 官網發生異常: {e}")
    sys.exit(1)

# 組裝對 Live API 發送的 POST 參數
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

print("🚀 正在對中職 Live API 發送 POST 請求...")
try:
    response_api = session.post(api_url, data=payload, timeout=15)
    if response_api.status_code == 200:
        raw_json = response_api.json()
        if raw_json.get("Success"):
            scoreboard = {}
            if "GameDetailJson" in raw_json and raw_json["GameDetailJson"]:
                game_detail = json.loads(raw_json["GameDetailJson"])
                for item in game_detail:
                    if item.get("GameSno") is not None and int(float(item.get("GameSno"))) == int(float(GAME_SNO)):
                        scoreboard = {
                            "狀態": item.get("GameStatusChi"),
                            "客隊": item.get("VisitingTeamName"),
                            "客隊分數": int(float(item.get("VisitingTotalScore", 0))),
                            "主隊": item.get("HomeTeamName"),
                            "主隊分數": int(float(item.get("HomeTotalScore", 0)))
                        }
                        break
            
            if scoreboard:
                live_logs = json.loads(raw_json.get("LiveLogJson", "[]"))
                balls, strikes, outs = 0, 0, 0
                if live_logs:
                    latest_pitch = live_logs[-1]
                    balls = int(float(latest_pitch.get("BallCnt", 0)))
                    strikes = int(float(latest_pitch.get("StrikeCnt", 0)))
                    outs = int(float(latest_pitch.get("OutCnt", 0)))
                
                final_data = {
                    "game_sno": int(GAME_SNO),
                    "v_team": scoreboard["客隊"],
                    "h_team": scoreboard["主隊"],
                    "v_score": scoreboard["客隊分數"],
                    "h_score": scoreboard["主隊分數"],
                    "balls": balls,
                    "strikes": strikes,
                    "outs": outs,
                    "status": scoreboard["狀態"]
                }
                
                with open("cpbl.json", "w", encoding="utf-8") as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=2)
                print("🎉 數據已成功依照規格書格式清洗並存入 cpbl.json！")
            else:
                print("❌ 【雙向驗證失敗】中職回傳列表中找不到指定的場號。")
                sys.exit(1)
        else:
            print("❌ 【API 錯誤】中職 API 回傳 Success 狀態為 False")
            sys.exit(1)
    else:
        print(f"❌ 【API 失敗】請求中職 Live API 失敗 (狀態碼: {response_api.status_code})")
        sys.exit(1)
except Exception as e:
    print(f"❌ 【執行異常】錯誤原因: {e}")
    sys.exit(1)
