import os
import json
import requests

API_KEY = "ms-2772ab7c-2db2-4fed-8395-1702cd8e2646"
BASE_URL = "https://modelscope.cn/openapi/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def whoami():
    url = f"{BASE_URL}/users/me"
    resp = requests.get(url, headers=HEADERS)
    return resp.json()

def create_studio(owner, repo_name):
    url = f"{BASE_URL}/studios"
    payload = {
        "owner": owner,
        "name": repo_name,
        "repo_type": "studio",
        "description": "高校宿舍智能AI管理系统 - 基于魔搭Qwen-1.8B-Chat大模型开发的高校宿舍智能化运维管理平台",
        "sdk_type": "gradio",
        "resource_configuration": "platform/2v-cpu-16g-mem",
        "base_image": "ubuntu22.04-py311-torch2.3.1-modelscope1.31.0"
    }
    resp = requests.post(url, headers=HEADERS, json=payload)
    return resp.json()

def deploy_studio(owner, repo_name):
    url = f"{BASE_URL}/studios/{owner}/{repo_name}/deploy"
    resp = requests.post(url, headers=HEADERS)
    return resp.json()

def get_studio(owner, repo_name):
    url = f"{BASE_URL}/studios/{owner}/{repo_name}"
    resp = requests.get(url, headers=HEADERS)
    return resp.json()

def upload_file(owner, repo_name, file_path, commit_message="Update files"):
    url = f"{BASE_URL}/studios/{owner}/{repo_name}/files"
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        data = {'commit_message': commit_message}
        resp = requests.post(url, headers=HEADERS, files=files, data=data)
    return resp.json()

def upload_folder(owner, repo_name, folder_path, commit_message="Update files"):
    url = f"{BASE_URL}/studios/{owner}/{repo_name}/files"
    files = []
    for filename in os.listdir(folder_path):
        if filename.startswith('.') or filename in ['output.txt', 'error.txt', 'deploy.py']:
            continue
        full_path = os.path.join(folder_path, filename)
        if os.path.isfile(full_path):
            files.append(('files', (filename, open(full_path, 'rb'))))
    data = {'commit_message': commit_message}
    resp = requests.post(url, headers=HEADERS, files=files, data=data)
    return resp.json()

def list_studios():
    url = f"{BASE_URL}/users/me/repos"
    resp = requests.get(url, headers=HEADERS)
    print(f"状态码: {resp.status_code}")
    print(f"响应内容: {resp.text[:500]}")
    try:
        return resp.json()
    except:
        return {"raw": resp.text[:500]}

if __name__ == "__main__":
    owner = "Maggie643"
    repo_name = "university-dorm-ai-management"
    
    print("🔍 验证身份...")
    user = whoami()
    if user.get("success"):
        print(f"✅ 认证成功！用户: {user['data']['username']}")
    else:
        print(f"❌ 认证失败: {user}")
        exit(1)
    
    print("\n📦 获取创空间信息...")
    studio = get_studio(owner, repo_name)
    print(f"创空间响应: {studio}")
    
    if not studio.get("success"):
        print("\n📝 创建创空间...")
        result = create_studio(owner, repo_name)
        print(f"创建结果: {result}")
        if not result.get("success"):
            print("❌ 创建失败，尝试其他创空间名称...")
            
            repo_name = "dorm-ai-management"
            studio = get_studio(owner, repo_name)
            if studio.get("success"):
                print(f"✅ 找到已有创空间: {repo_name}")
            else:
                result = create_studio(owner, repo_name)
                print(f"创建结果: {result}")
    
    print("\n📦 获取创空间信息(第二次尝试)...")
    studio = get_studio(owner, repo_name)
    print(f"创空间响应: {studio}")
    
    print("\n🚀 尝试部署...")
    result = deploy_studio(owner, repo_name)
    print(f"部署结果: {result}")