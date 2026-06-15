import requests, json

GAS_URL = "https://script.google.com/macros/s/AKfycbwsJCQXg7Ilzvdv7Jei6BP8AaQ4_uGr3PMH3WupkzaBcVw0kU2NQVumS7ivJCo3ACkq/exec"

try:
    res = requests.get(GAS_URL, timeout=20)
    data = res.json()
    if "error" in data: raise Exception(data["error"])
    with open("cpbl.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 更新完成: {data['v_team']} {data['v_score']} : {data['h_team']} {data['h_score']}")
except Exception as e:
    print(f"❌ 失敗: {e}")
    exit(1)
