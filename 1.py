import requests
import json
import time

GAS_URL = "https://script.googleusercontent.com/macros/echo?user_content_key=AUkAhnSMHjH8kwbduHPEN2Tgi2DVWCQWG_KGQYYPbRqlVahxG5xAGMnGu_XFdhOU8aVyvqzdcLFoh8ihbGRVkkTuFaw5v2BtXH_Uj3Z_IjiyQlQ3Q61I22cZR0uXqoaM2m7cWPXPc6Z0oYwg7uHbdAFbkYkx-iw2_Kj-N6c3ANFAkyPsyvL4SraM9bIf_cQL3pZfv1ocWrJ5ilBU1CI3M0FUnDGohdEksu9FxAGd7faLzR2fb_xWSJoUgbo46EFmpmNnzP9s0KMJpqSddIN-FYCBuwlfAwKBag&lib=M2LHac6VRrvq7A3NOANO4ZYtiO8R5qc0s"

def debug_print(msg):
    print(f"[DEBUG] {time.strftime('%H:%M:%S')} - {msg}")

try:
    debug_print("正在從 GAS 中繼站獲取數據...")
    res = requests.get(GAS_URL, timeout=20)
    res.raise_for_status()
    
    # 🔍 關鍵偵錯：先印出原始文字，看看到底是不是 JSON
    print("--- GAS 回傳原始內容開頭 ---")
    print(res.text[:500]) 
    print("--- GAS 回傳原始內容結尾 ---")
    
    final_data = res.json()
    
    if "error" in final_data:
        raise Exception(f"GAS 端發生錯誤: {final_data['error']}")
        
    with open("cpbl.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    debug_print("cpbl.json 檔案更新成功。")

except Exception as e:
    print(f"❌ 失敗: {str(e)}")
    raise e
