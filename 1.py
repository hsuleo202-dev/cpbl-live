import os
import sys
import json
import requests

# ====================================================================
# 🎯 CPBL 看板系統 GitHub 輕量端 (v4.0 - 1.py GET 穩定版)
# ====================================================================

# 保持您目前的最新 GAS 網址不變
GAS_URL = "https://script.google.com/macros/s/AKfycbyuD3I4TwsnfZLEl_OC7OV1gAE3cK-rba4CZdM27D2XHtZt3DR0L5V2PsC1yfXFS7fO/exec"
def main():
    print("🔄 正在向全新 GAS 中樞請求即時賽況清洗數據 (GET 模式)...")
    try:
        # 核心修正：改用 get 請求，徹底避開 Google 對 POST 的 405 限制
        # 同時帶上 action=fetch 參數，讓 GAS 知道這是 GitHub 要來拿資料
        response = requests.get(f"{GAS_URL}?action=fetch", timeout=25)
        
        if response.status_code != 200:
            print(f"❌ GAS 回傳狀態錯誤，HTTP 代碼: {response.status_code}")
            sys.exit(1)
            
        res_json = response.json()
        status = res_json.get("status")
        
        if status == "skip":
            print(f"⏩ 觸發防重疊鎖定保護機制: {res_json.get('message')}")
            sys.exit(0)
            
        elif status == "error":
            print(f"❌ GAS 雲端核心內部執行失敗: {res_json.get('message')}")
            sys.exit(1)
            
        elif status == "success" and "data" in res_json:
            final_data = res_json["data"]
            
            # 將高精準度輕量 JSON 覆寫存入 cpbl.json
            with open("cpbl.json", "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
                
            print(f"🎉 數據雙向場號驗證清洗成功！")
            print(f"📊 當前賽況 -> 場次: {final_data['game_sno']} | {final_data['v_team']} {final_data['v_score']} : {final_data['h_score']} {final_data['h_team']}")
            
        else:
            print("❌ 未知或不相容的 GAS 回傳格式")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 網路傳輸或 JSON 解析發生異常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
