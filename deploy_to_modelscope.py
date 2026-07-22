import requests

API_KEY = "ms-2772ab7c-2db2-4fed-8395-1702cd8e2646"
BASE_URL = "https://modelscope.cn/openapi/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

OWNER = "Maggie643"
REPO_NAME = "dorm-ai-management"

def deploy():
    url = f"{BASE_URL}/studios/{OWNER}/{REPO_NAME}/deploy"
    print("🚀 开始部署...")
    resp = requests.post(url, headers=HEADERS, timeout=60)
    print(f"   状态码: {resp.status_code}")
    
    try:
        result = resp.json()
        print(f"   结果: {result}")
        return result.get("success", False)
    except:
        print(f"   响应: {resp.text[:500]}")
        return False

def get_status():
    url = f"{BASE_URL}/studios/{OWNER}/{REPO_NAME}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    try:
        result = resp.json()
        if result.get("success"):
            data = result.get("data", {})
            print(f"\n📋 创空间状态:")
            print(f"   名称: {data.get('display_name')}")
            print(f"   URL: {data.get('url')}")
            print(f"   状态: {data.get('status')}")
            print(f"   SDK类型: {data.get('sdk_type')}")
            print(f"   资源配置: {data.get('resource_configuration')}")
            return data.get("status")
    except:
        print(f"❌ 获取状态失败: {resp.text[:200]}")
    return None

if __name__ == "__main__":
    deploy_success = deploy()
    
    if deploy_success:
        print("\n🎉 部署请求已提交！")
        print(f"📋 创空间地址: https://modelscope.cn/studios/{OWNER}/{REPO_NAME}")
        
        print("\n🔄 检查部署状态...")
        status = get_status()
        if status:
            print(f"   当前状态: {status}")
            print("\n💡 提示: 部署需要5-10分钟，请耐心等待。")
    else:
        print("\n❌ 部署失败，请稍后重试。")