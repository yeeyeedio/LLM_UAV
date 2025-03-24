# ollama_airsim.py

import requests  # 用于调用 Ollama 本地 API
import re  # 正则表达式库，用于从文本中提取代码块
import argparse  # 用于解析命令行参数
from airsim_wrapper import *  # 导入前面定义的 AirSimWrapper 类
import os  # 用于与操作系统交互，例如清屏
import json  # 用于处理 JSON 数据

# 解析命令行参数
parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="prompts/airsim_basic.txt")
parser.add_argument("--sysprompt", type=str, default="system_prompts/airsim_basic.txt")
args = parser.parse_args()

# 读取系统提示（系统向导提示信息）
with open(args.sysprompt, "r", encoding="utf-8") as f:
    sysprompt = f.read()

# 设置初始的聊天记录，包括系统提示和一个简单的用户请求示例
chat_history = [
    {"role": "system", "content": sysprompt},
    {"role": "user", "content": "向前是正 X 轴方向(X增大代表飞行向前，减小代表飞行向后)。向右是正 Y 轴方向(Y增大代表飞行向右，减小代表飞行向左)。向下是正 Z 轴方向(Z增大代表飞行向下，减小代表飞行向上)。例如，要向前移动10个单位，向右移动20个单位，向上移动30个单位，应该表示为(x+10,y+20,z-30)。请向上移动 10 个单位"},
    {"role": "assistant", "content": """```python
aw.fly_to([aw.get_drone_position()[0], aw.get_drone_position()[1], aw.get_drone_position()[2]-10])
```

这段代码使用了 `fly_to()` 函数，将无人机移动到当前位置上方的 10 个单位。它通过调用 `get_drone_position()` 获取当前无人机的位置，然后创建一个新的列表，保持相同的 X 和 Y 坐标，但将 Z 坐标减少了 10。然后，无人机会通过 `fly_to()` 函数飞到这个新位置。"""}
]

# 调用本地Ollama的DeepSeek模型
def ask(prompt):
    chat_history.append({"role": "user", "content": prompt})

    url = "http://localhost:11434/api/chat"
    data = {"model": "deepseek-r1:1.5b", "messages": chat_history, "stream": False}

    response = requests.post(url, json=data).json()
    reply = response["message"]["content"]

    chat_history.append({"role": "assistant", "content": reply})

    return reply

# 提取响应中的 Python 代码
def extract_python_code(content):
    code_blocks = re.findall(r"```(.*?)```", content, re.DOTALL)
    if code_blocks:
        full_code = "\n".join(code_blocks)
        if full_code.startswith("python"):
            full_code = full_code[7:]
        return full_code
    return None

# 定义颜色类，用于终端输出彩色文本
class colors:
    RED = "\033[31m"
    ENDC = "\033[m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"

# 初始化 AirSim 客户端
print("正在初始化 AirSim...")
aw = AirSimWrapper()
print("完成.")

# 读取并发送启动提示信息
with open(args.prompt, "r", encoding="utf-8") as f:
    prompt = f.read()

ask(prompt)
print("欢迎来到 AirSim 聊天机器人！我随时准备帮助你解答 AirSim 相关的问题和命令。")

# 进入命令行交互模式
while True:
    question = input(colors.YELLOW + "AirSim> " + colors.ENDC)

    if question in ["!quit", "!exit"]:
        break
    if question == "!clear":
        os.system("cls")
        continue

    response = ask(question)
    print(f"\n{response}\n")

    code = extract_python_code(response)
    if code:
        print("请稍等，我正在 AirSim 中运行代码...")
        exec(code)
        print("完成！\n")
