import requests
import os

API_KEY = "ms-2772ab7c-2db2-4fed-8395-1702cd8e2646"
BASE_URL = "https://modelscope.cn/openapi/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

OWNER = "Maggie643"
REPO_NAME = "dorm-ai-management"

def upload_files():
    url = f"{BASE_URL}/studios/{OWNER}/{REPO_NAME}/files"
    
    files_to_upload = [
        "app.py",
        "db.py",
        "ai_engine.py", 
        "workflow.py",
        "requirements.txt",
        "ms_deploy.json",
        "README.md"
    ]
    
    open_files = []
    files = []
    try:
        for filename in files_to_upload:
            if os.path.exists(filename):
                f = open(filename, 'rb')
                open_files.append(f)
                files.append(('files', (filename, f)))
                print(f"   ✅ 准备上传: {filename}")
            else:
                print(f"   ⚠️ 文件不存在: {filename}")
        
        if not files:
            print("❌ 没有可上传的文件")
            return False
        
        print("\n📤 上传文件...")
        resp = requests.post(url, headers=HEADERS, files=files, timeout=120)
        print(f"   状态码: {resp.status_code}")
        
        try:
            result = resp.json()
            print(f"   结果: {result}")
            return result.get("success", False)
        except:
            print(f"   响应: {resp.text[:500]}")
            return False
    finally:
        for f in open_files:
            f.close()

def deploy():
    url = f"{BASE_URL}/studios/{OWNER}/{REPO_NAME}/deploy"
    print("\n🚀 开始部署...")
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
    print("📦 上传项目文件到创空间...")
    upload_success = upload_files()
    
    if upload_success:
        print("\n✅ 文件上传成功！")
        
        print("\n🚀 部署创空间...")
        deploy_success = deploy()
        
        if deploy_success:
            print("\n🎉 部署请求已提交！")
            print(f"📋 创空间地址: https://modelscope.cn/studios/{OWNER}/{REPO_NAME}")
            
            print("\n🔄 检查部署状态...")
            status = get_status()
            if status:
                print(f"   当前状态: {status}")
                print("\n💡 提示: 部署需要5-10分钟，请耐心等待。")
                print("   您可以访问上面的链接查看部署进度。")
        else:
            print("\n❌ 部署失败，请稍后重试。")
    else:
        print("\n❌ 文件上传失败，请检查网络连接。")