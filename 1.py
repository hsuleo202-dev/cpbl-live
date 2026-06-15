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
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Referer': 'https://www.cpbl.com.tw/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
})

def debug_print(msg):
    print(f"[DEBUG] {time.strftime('%H:%M:%S')} - {msg}")

def safe_int_cast(val, default=0):
    """安全轉換型態函數，防止 NoneType 或空字串導致 float() / int() 崩潰"""
    if val is None or str(val).strip() == "":
        return default
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return default

# ====================================================================
# 🚀 全自動化邏輯核心
# ====================================================================
try:
    debug_print("開始嘗試連接 GAS 獲取場次資訊...")
    res_gas = session.get(GAS_URL, timeout=15)
    res_gas.raise_for_status()
    data = res_gas.json()
    GAME_SNO, GAS_DATE = str(data["game_sno"]), data["date"]
    YEAR, MONTH = GAS_DATE.split('/')[0], str(int(GAS_DATE.split('/')[1]))
    debug_print(f"成功獲取目標場次: {GAME_SNO} ({GAS_DATE})")

    debug_print("正在請求官網獲取 Token...")
    # 先請求首頁獲取合法 Session
    session.get("https://www.cpbl.com.tw/", timeout=15)
    time.sleep(random.uniform(1, 3))
    
    idx_url = f"https://www.cpbl.com.tw/box/index?gameSno={GAME_SNO}&year={YEAR}&kindCode=A"
    res_index = session.get(idx_url, timeout=15)
    
    if res_index.status_code == 403:
        raise Exception("遭中職防火牆封鎖 (403 Forbidden)")
    
    token_match = re.search(r'__RequestVerificationToken"\s+type="hidden"\s+value="(.*?)"', res_index.text)
    if not token_match:
        raise Exception("無法從官網頁面提取 Token")
    fresh_token = token_match.group(1)

    debug_print("發送 Live API 請求...")
    payload = {
        '__RequestVerificationToken': fresh_token,
        'GameSno': GAME_SNO, 'KindCode': 'A', 'Year': YEAR,
        'PrevOrNext': '0', 'SelectKindCode': 'A',
        'SelectYear': YEAR, 'SelectMonth': MONTH
    }
    res_api = session.post("https://www.cpbl.com.tw/box/getlive", data=payload, timeout=15)
    
    if res_api.status_code != 200:
        raise Exception(f"API 請求失敗，狀態碼: {res_api.status_code}")

    raw = res_api.json()
    if not raw.get("Success"):
        raise Exception("API 回傳 Success: False")

    # 解析資料
    game_detail = json.loads(raw.get("GameDetailJson", "[]"))
    
    # 這裡也加上防空保護，避免比對 GameSno 時崩潰
    scoreboard = {}
    for item in game_detail:
        item_sno = item.get("GameSno")
        if item_sno is not None and safe_int_cast(item_sno) == safe_int_cast(GAME_SNO):
            scoreboard = item
            break

    live_logs = json.loads(raw.get("LiveLogJson", "[]"))
    latest = live_logs[-1] if live_logs else {}

    # 使用 safe_int_cast 徹底解決 float() argument must be a string... 錯誤
    final_data = {
        "game_sno": safe_int_cast(GAME_SNO),
        "v_team": scoreboard.get("VisitingTeamName", "未知"),
        "h_team": scoreboard.get("HomeTeamName", "未知"),
        "v_score": safe_int_cast(scoreboard.get("VisitingTotalScore")),
        "h_score": safe_int_cast(scoreboard.get("HomeTotalScore")),
        "balls": safe_int_cast(latest.get("BallCnt")),
        "strikes": safe_int_cast(latest.get("StrikeCnt")),
        "outs": safe_int_cast(latest.get("OutCnt")),
        "status": scoreboard.get("GameStatusChi", "未開賽")
    }

    with open("cpbl.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    debug_print("檔案更新成功，任務結束。")

except Exception as e:
    print(f"❌ 發生致命錯誤: {str(e)}")
    raise e
