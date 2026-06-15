import os
import sys
import json
import requests

# ====================================================================
# 🎯 CPBL 看板系統 GitHub 輕量端 (v4.0 - 1.py 最終定案版)
# ====================================================================

# 已全面同步為您手動驗證通暢後的最新 GAS 雲端網址
GAS_URL = "https://script.googleusercontent.com/macros/echo?user_content_key=AUkAhnRoW1J_AVldskB8uZPCloQZcQApJM-0Lk3LhhLqY5qigNhQSk4ZJ8EWVNbc_NBCs9BbpJfmn7s4C9kADR19Gj1krNl3iV_DeT_hyYm1mUFaCtRXvaQPy7DKr_AeQX8bMY7isy2ShdHjlW6qCCwUKtXcI5tSw9PeiwdlfFyiUic3aPzyBECEWgw7RVnOI-J1ZaehFJKFscQb7kGeM5bBcOiWPvFAsInMJjg8ZppuJgeQtf-0ym8xYH-MG_SjOJGFl1A52TthGylSZookZc5UaWlq3UIAYw&lib=M2LHac6VRrvq7A3NOANO4ZYtiO8R5qc0s"

def main():
    print("🔄 正在向全新 GAS 中樞請求即時賽況清洗數據...")
    try:
        # 向 GAS 發送 POST 請求觸發動態安全驗證與賽況清洗
        response = requests.post(GAS_URL, timeout=25)
        
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
            
            # 將高精準度輕量 JSON 覆寫存入 cpbl.json，供 Wi-Fi 晶片每分鐘輪詢
            with open("cpbl.json", "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
                
            print(f"🎉 數據雙向場號驗證清洗成功！")
            print(f"📊 當前賽況 -> 場次: {final_data['game_sno']} | {final_data['v_team']} {final_data['v_score']} : {final_data['h_score']} {final_data['h_team']} | 球數: {final_data['balls']}B-{final_data['strikes']}S-{final_data['outs']}O")
            
        else:
            print("❌ 未知的 GAS 核心回傳格式")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 網路傳輸或 JSON 解析發生異常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
