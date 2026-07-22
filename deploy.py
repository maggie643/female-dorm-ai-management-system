import os
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MODELscope_API_KEY")
OWNER = "Maggie643"
REPO_NAME = "dorm-ai-management"
BASE_URL = "https://modelscope.cn/openapi/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def test_api():
    print("🔍 测试API连接...")
    url = f"{BASE_URL}/users/me"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        print(f"   状态码: {resp.status_code}")
        if resp.status_code == 200:
            print("   ✅ API连接成功")
        else:
            print(f"   ❌ API连接失败: {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

def push_to_modelscope():
    print("\n📤 推送到魔搭仓库...")
    git_url = f"https://oauth2:{API_KEY}@www.modelscope.cn/studios/{OWNER}/{REPO_NAME}.git"
    
    result = subprocess.run(
        ["git", "push", git_url, "main"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        print("   ✅ 推送成功")
    else:
        print(f"   ❌ 推送失败: {result.stderr[:300]}")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ 请在.env文件中设置MODELscope_API_KEY")
        exit(1)
    
    test_api()
    push_to_modelscope()
