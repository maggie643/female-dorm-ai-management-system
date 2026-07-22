import subprocess
import os
import requests

API_KEY = "ms-2772ab7c-2db2-4fed-8395-1702cd8e2646"
BASE_URL = "https://modelscope.cn/openapi/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

OWNER = "Maggie643"
REPO_NAME = "dorm-ai-management"

def get_git_url():
    url = f"{BASE_URL}/studios/{OWNER}/{REPO_NAME}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    try:
        result = resp.json()
        if result.get("success"):
            data = result.get("data", {})
            git_url = data.get("git_url")
            print(f"📋 创空间信息:")
            print(f"   名称: {data.get('display_name')}")
            print(f"   URL: {data.get('url')}")
            print(f"   Git URL: {git_url}")
            return git_url
    except:
        print(f"❌ 获取信息失败: {resp.text[:200]}")
    return None

def deploy():
    url = f"{BASE_URL}/studios/{OWNER}/{REPO_NAME}/deploy"
    resp = requests.post(url, headers=HEADERS, timeout=60)
    try:
        result = resp.json()
        print(f"   状态码: {resp.status_code}")
        print(f"   结果: {result}")
        return result.get("success", False)
    except:
        print(f"   响应: {resp.text[:500]}")
        return False

if __name__ == "__main__":
    print("🔍 获取创空间Git地址...")
    git_url = get_git_url()
    
    if not git_url:
        print("❌ 无法获取Git地址，尝试构建标准地址...")
        git_url = f"https://oauth2:{API_KEY}@www.modelscope.cn/studios/{OWNER}/{REPO_NAME}.git"
        print(f"   使用标准地址: {git_url}")
    
    temp_dir = f"temp_{REPO_NAME}"
    if os.path.exists(temp_dir):
        subprocess.run(["rmdir", "/s", "/q", temp_dir], shell=True)
    
    print("\n📥 克隆仓库...")
    result = subprocess.run(
        ["git", "clone", git_url, temp_dir],
        capture_output=True,
        text=True,
        timeout=120
    )
    print(f"   返回码: {result.returncode}")
    if result.returncode != 0:
        print(f"   ❌ 克隆失败: {result.stderr[:300]}")
        exit(1)
    
    print("\n📤 复制文件到仓库...")
    files_to_copy = [
        "app.py", "db.py", "ai_engine.py", "workflow.py",
        "requirements.txt", "ms_deploy.json", "README.md"
    ]
    
    current_dir = os.getcwd()
    os.chdir(temp_dir)
    
    for f in files_to_copy:
        src = os.path.join(current_dir, f)
        if os.path.exists(src):
            subprocess.run(["copy", src, f], shell=True, capture_output=True)
            print(f"   ✅ {f}")
        else:
            print(f"   ❌ 文件不存在: {f}")
    
    print("\n📝 Git提交...")
    subprocess.run(["git", "config", "user.email", "deploy@modelscope.cn"], capture_output=True)
    subprocess.run(["git", "config", "user.name", "DeployBot"], capture_output=True)
    subprocess.run(["git", "add", "."], capture_output=True)
    
    result = subprocess.run(
        ["git", "commit", "-m", "Update dorm management system code"],
        capture_output=True,
        text=True
    )
    print(f"   提交结果: {result.stdout[:200]}")
    
    print("\n📤 Git推送...")
    result = subprocess.run(
        ["git", "push", "origin", "master"],
        capture_output=True,
        text=True,
        timeout=120
    )
    print(f"   返回码: {result.returncode}")
    if result.returncode != 0:
        print(f"   ❌ 推送失败: {result.stderr[:300]}")
        os.chdir(current_dir)
        subprocess.run(["rmdir", "/s", "/q", temp_dir], shell=True)
        exit(1)
    
    print("✅ 推送成功！")
    
    os.chdir(current_dir)
    subprocess.run(["rmdir", "/s", "/q", temp_dir], shell=True)
    
    print("\n🚀 部署创空间...")
    deploy_success = deploy()
    
    if deploy_success:
        print("\n🎉 部署请求已提交！")
        print(f"📋 创空间地址: https://modelscope.cn/studios/{OWNER}/{REPO_NAME}")
        print("\n💡 提示: 部署需要5-10分钟，请耐心等待。")
    else:
        print("\n❌ 部署失败，请稍后手动触发部署。")