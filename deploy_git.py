import subprocess
import os

API_KEY = "ms-2772ab7c-2db2-4fed-8395-1702cd8e2646"
OWNER = "Maggie643"

studio_names = [
    "university-dorm-ai-management",
    "female-dorm-ai-management-system",
    "dorm-management-system"
]

for repo_name in studio_names:
    print(f"\n🔍 尝试创空间: {repo_name}")
    
    git_url = f"https://oauth2:{API_KEY}@www.modelscope.cn/studios/{OWNER}/{repo_name}.git"
    
    print("   检查git仓库...")
    try:
        result = subprocess.run(
            ["git", "ls-remote", git_url],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ 找到创空间: {repo_name}")
            
            temp_dir = f"temp_{repo_name}"
            if os.path.exists(temp_dir):
                subprocess.run(["rm", "-rf", temp_dir], shell=True)
            
            print("   克隆仓库...")
            result = subprocess.run(
                ["git", "clone", git_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print("✅ 克隆成功")
                
                files_to_copy = [
                    "app.py", "db.py", "ai_engine.py", "workflow.py",
                    "requirements.txt", "ms_deploy.json", "README.md"
                ]
                
                print("   复制文件...")
                for f in files_to_copy:
                    if os.path.exists(f):
                        subprocess.run(
                            ["copy", f, os.path.join(temp_dir, f)],
                            shell=True,
                            capture_output=True
                        )
                        print(f"      ✅ {f}")
                
                os.chdir(temp_dir)
                print("   添加文件...")
                subprocess.run(["git", "add", "."], capture_output=True)
                
                print("   提交...")
                subprocess.run(
                    ["git", "commit", "-m", "Update dorm management system code"],
                    capture_output=True
                )
                
                print("   推送...")
                result = subprocess.run(
                    ["git", "push", "origin", "master"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    print("✅ 推送成功！")
                    print(f"📋 创空间地址: https://modelscope.cn/studios/{OWNER}/{repo_name}")
                    os.chdir("..")
                    subprocess.run(["rm", "-rf", temp_dir], shell=True)
                    exit(0)
                else:
                    print(f"❌ 推送失败: {result.stderr[:200]}")
            else:
                print(f"❌ 克隆失败: {result.stderr[:200]}")
        else:
            print(f"❌ 创空间不存在: {repo_name}")
    except Exception as e:
        print(f"❌ 错误: {e}")

print("\n❌ 所有创空间都尝试过了，请手动创建创空间后再试")