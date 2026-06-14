import requests
import json
from datetime import datetime
import timezonefinder  # 如果需要處理時區，或直接用簡化時間

# 🚀 自動取得今天台灣時間的年、月、日
# GitHub 伺服器預設是 UTC 時間，我們手動加 8 小時修正為台灣時間
from datetime import timedelta
now_tw = datetime.utcnow() + timedelta(hours=8)
YEAR = now_tw.strftime("%Y")
MONTH = str(int(now_tw.strftime("%m")))  # 去除前導零，例如 "06" 變成 "6"
DATE_STR = now_tw.strftime("%Y/%m/%d")

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
})

print(f"📅 機器人啟動！正在查詢今天 ({DATE_STR}) 的賽程...")

# 第一步：直接抓取整個月的賽程表表單
schedule_url = f"https://www.cpbl.com.tw/schedule/index?year={YEAR}&month={MONTH}&kindCode=A"
response_sched = session.get(schedule_url)

target_game_sno = None

if response_sched.status_code == 200:
    # 尋找今天的比賽區塊
    # 中職官網賽程表的 HTML 會包含日期的文字
    html_text = response_sched.text
    
    # 我們在網頁裡尋找有沒有包含「味全」以及今天的日期
    # 這裡實作自動尋找今天賽程中含有味全龍的 GameSno
    import re
    # 尋找當天賽程區塊的簡易邏輯：找出所有的比賽場次與隊伍
    # 為了百分之百精準，我們直接比對中職官網當天的所有比賽
    # 透過正則表達式撈出遊戲編號
    games = re.findall(r'gameSno=(\d+).*?year='+YEAR, html_text)
    
    # 為了簡化晶片端的負擔，我們直接幫你走訪今天這月份的賽程
    # 尋找符合今天日期且帶有 "味全" 關鍵字的欄位
    # 我們這邊用一個最穩定的官方 API 邏輯：
    # 直接用對方的功課表比對，如果今天有味全的比賽，撈出它的 GameSno
    
    # 簡化測試：我們讓機器人直接去爬今天的所有場次，看哪一場有味全
    # 這裡我們用一個更萬無一失的做法：尋找包含 gameSno 的連結，並檢查前後文是否有味全
    # 找尋官網 HTML 中的比賽場次
    matches = re.findall(r'gameSno=(\d+)&year='+YEAR+'&kindCode=A', html_text)
    # 去重
    matches = list(set(matches))
    
    for sno in matches:
        # 測試每一場比賽的網頁內容，看是不是今天的比賽，而且有沒有味全
        box_url = f"https://www.cpbl.com.tw/box/index?gameSno={sno}&year={YEAR}&kindCode=A"
        res_box = session.get(box_url)
        if res_box.status_code == 200 and DATE_STR in res_box.text and "味全" in res_box.text:
            target_game_sno = sno
            print(f"🎯 找到了！今天有味全龍的比賽！場次編號：{target_game_sno}")
            break

if not target_game_sno:
    print("💤 今天沒有味全龍的比賽，或者比賽尚未開打。機器人自動收工，不更新檔案。")
    exit()

# 第二步：既然有味全的比賽，開始抓取即時比分 JSON
index_url = f"https://www.cpbl.com.tw/box/index?gameSno={target_game_sno}&year={YEAR}&kindCode=A"
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
        'GameSno': target_game_sno,
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
        
        # 把今天的日期和場次一起塞進 JSON 裡面，讓晶片可以讀到
        raw_json['custom_info'] = {
            'date': DATE_STR,
            'game_sno': target_game_sno,
            'team_filter': '味全龍'
        }
        
        with open("cpbl.json", "w", encoding="utf-8") as f:
            json.dump(raw_json, f, ensure_ascii=False, indent=4)
        print("🎉 成功更新今日味全龍賽事數據至 cpbl.json！")
