# 部署凌逍资产管理到 PythonAnywhere（免费，无需信用卡）

## 第一步：注册 PythonAnywhere 账号

1. 访问 https://www.pythonanywhere.com
2. 点击 **Pricing & signup** → 选择 **Create a Beginner account**（免费套餐）
3. 填写用户名、邮箱、密码完成注册
4. 登录后进入 Dashboard

---

## 第二步：打开 Bash 控制台

1. 在 Dashboard 顶部菜单点击 **Consoles** → **Bash**
2. 在打开的终端中，克隆代码仓库：

```bash
git clone https://github.com/Rosalind-502106/lingxiao-lab.git
```

3. 进入项目目录并安装依赖：

```bash
cd lingxiao-lab
pip install --user -r requirements.txt
```

---

## 第三步：配置 Web 应用

1. 点击顶部菜单 **Web** → **Add a new web app**
2. 点击 **Next** → 选择 **Manual configuration** → 选择 **Python 3.10**
3. 配置以下内容：

### Virtualenv（虚拟环境）
在 Web 页面的 **Virtualenv** 部分，输入路径：
```
/home/你的用户名/.local
```
然后点击绿色勾 ✅

### Code 部分
- **Source code:** `/home/你的用户名/lingxiao-lab`
- **Working directory:** `/home/你的用户名/lingxiao-lab`

### WSGI 配置文件
1. 点击 **WSGI configuration file** 链接（蓝色文字）
2. 删除全部内容，粘贴以下代码：

```python
import sys
import os

path = '/home/你的用户名/lingxiao-lab'
if path not in sys.path:
    sys.path.append(path)

os.chdir(path)

from app import app as application
```

3. 点击 **Save**

---

## 第四步：启动 Web 应用

1. 回到 Web 页面顶部
2. 点击 **Reload 你的用户名.pythonanywhere.com**
3. 等待几秒钟，状态变为绿色 **Reloaded successfully**

---

## 第五步：访问你的网站

访问 https://你的用户名.pythonanywhere.com

---

## 更新代码

以后如果 GitHub 上的代码有更新，在 Bash 中运行：

```bash
cd ~/lingxiao-lab
git pull
pip install --user -r requirements.txt  # 如果有新依赖
```

然后回到 Web 页面点 **Reload** 即可。

---

## 注意事项

- PythonAnywhere 免费套餐的网站会有 3 个月不访问自动休眠，再次访问时会自动唤醒（约等10秒）
- 数据存储在 `lab_data.json` 文件中，备份请下载此文件
- 建议在 Web 页面的 Environment variables 中设置：
  - `SECRET_KEY` = 一个随机字符串
  - `ADMIN_PASSWORD` = 管理员密码