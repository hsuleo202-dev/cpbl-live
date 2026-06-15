import os
import sys
import json
import requests

# ====================================================================
# 🎯 CPBL 看板系統 GitHub 輕量端 (v4.0 - E.py)
# ====================================================================

# 請將此處替換為您上方部署好的完整 GAS 網頁應用程式部署網址
GAS_URL = "https://script.google.com/macros/s/AKfycbxTanVcltBfB8WdmuPQBig1HalQCqYJJLzJyrGGoJVMNVjq0IO4jbLsPzQr9P7J96SC/exec"

def main():
    print("🔄 正在向 GAS 中樞請求即時賽況清洗數據...")
    try:
        # 向 GAS 發送 POST 請求觸發數據清洗流程
        response = requests.post(GAS_URL, timeout=25)
        
        if response.status_code != 200:
            print(f"❌ GAS 回傳錯誤代碼: {response.status_code}")
            sys.exit(1)
            
        res_json = response.json()
        status = res_json.get("status")
        
        if status == "skip":
            print(f"⏩ 跳過執行: {res_json.get('message')}")
            sys.exit(0)
            
        elif status == "error":
            print(f"❌ GAS 內部執行失敗: {res_json.get('message')}")
            sys.exit(1)
            
        elif status == "success" and "data" in res_json:
            final_data = res_json["data"]
            
            # 將高精準度輕量 JSON 寫入專案根目錄，供 Wi-Fi 晶片每分鐘輪詢
            with open("cpbl.json", "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
                
            print(f"🎉 數據驗證清洗成功！目前場次: {final_data['game_sno']} | {final_data['v_team']} {final_data['v_score']} : {final_data['h_score']} {final_data['h_team']}")
            
        else:
            print("❌ 未知的 GAS 回傳格式")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 網路連線或解析發生異常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
