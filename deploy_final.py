import requests

API_KEY = "ms-2772ab7c-2db2-4fed-8395-1702cd8e2646"
BASE_URL = "https://modelscope.cn/openapi/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def test_api():
    print("🔍 测试API连接...")
    
    endpoints = [
        "/users/me",
        "/studios/hardware?sdk_type=gradio",
        "/studios/sdk_versions?sdk_type=gradio"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            print(f"\n📡 {endpoint}")
            print(f"   状态码: {resp.status_code}")
            try:
                data = resp.json()
                print(f"   成功: {data.get('success', False)}")
                if 'data' in data:
                    print(f"   数据: {str(data['data'])[:300]}")
            except:
                print(f"   响应: {resp.text[:300]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

def create_studio_v2(owner, repo_name, display_name):
    url = f"{BASE_URL}/studios"
    payload = {
        "owner": owner,
        "name": repo_name,
        "repo_name": repo_name,
        "display_name": display_name,
        "repo_type": "studio",
        "description": "高校宿舍智能AI管理系统 - 基于魔搭Qwen-1.8B-Chat大模型开发的高校宿舍智能化运维管理平台",
        "sdk_type": "gradio",
        "resource_configuration": "platform/2v-cpu-16g-mem",
        "base_image": "ubuntu22.04-py311-torch2.3.1-modelscope1.31.0",
        "is_public": True,
        "license": "Apache-2.0"
    }
    print(f"\n📝 创建创空间: {repo_name}")
    print(f"   请求体: {payload}")
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=60)
    print(f"   状态码: {resp.status_code}")
    try:
        result = resp.json()
        print(f"   结果: {result}")
        return result
    except:
        print(f"   响应: {resp.text[:500]}")
        return {"success": False, "raw": resp.text}

if __name__ == "__main__":
    test_api()
    
    print("\n" + "="*50)
    print("尝试创建创空间...")
    print("="*50)
    
    create_studio_v2(
        owner="Maggie643",
        repo_name="dorm-ai-management",
        display_name="高校宿舍智能AI管理系统"
    )