import subprocess
import os

API_KEY = "ms-2772ab7c-2db2-4fed-8395-1702cd8e2646"
OWNER = "Maggie643"
REPO_NAME = "dorm-ai-management"

git_url = f"https://oauth2:{API_KEY}@www.modelscope.cn/studios/{OWNER}/{REPO_NAME}.git"
temp_dir = f"temp_{REPO_NAME}"

if os.path.exists(temp_dir):
    subprocess.run(["rmdir", "/s", "/q", temp_dir], shell=True)

print("📥 克隆魔搭仓库...")
result = subprocess.run(
    ["git", "clone", git_url, temp_dir],
    capture_output=True,
    text=True,
    timeout=120
)
if result.returncode != 0:
    print(f"❌ 克隆失败: {result.stderr[:300]}")
    exit(1)

print("✅ 克隆成功")

print("\n📤 复制文件...")
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
    ["git", "commit", "-m", "fix: 修复Gradio 6.x兼容性并优化UI"],
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

os.chdir(current_dir)
subprocess.run(["rmdir", "/s", "/q", temp_dir], shell=True)

if result.returncode == 0:
    print("✅ 推送到魔搭成功！")
else:
    print(f"❌ 推送失败: {result.stderr[:300]}")
    exit(1)