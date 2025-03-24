# deepseek_airsim.py

import openai  # 用于与 DeepSeek API 进行交互
import re  # 正则表达式库，用于从文本中提取代码块
import argparse  # 用于解析命令行参数
from airsim_wrapper import *  # 导入前面定义的 AirSimWrapper 类
import math  # 数学库
import numpy as np  # Numpy 库
import os  # 用于与操作系统交互，例如清屏
import json  # 用于处理 JSON 数据
import time  # 用于时间操作

# 解析命令行参数
parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="prompts/airsim_basic.txt")  # 默认读取基本提示文件
parser.add_argument("--sysprompt", type=str, default="system_prompts/airsim_basic.txt")  # 系统提示文件
args = parser.parse_args()  # 解析参数

# 读取配置文件（包含 API 密钥）
with open("config.json", "r") as f:
    config = json.load(f)

print("正在初始化 DeepSeek...")
openai.api_key = config["DEEPSEEK_API_KEY"]  # 设置 DeepSeek API 密钥
openai.api_base = "https://api.deepseek.com"  # 设置 DeepSeek API 的基础 URL
print("完成.")

# 读取系统提示（系统向导提示信息）
with open(args.sysprompt, "r", encoding="utf-8") as f:
    sysprompt = f.read()

# 设置初始的聊天记录，包括系统提示和一个简单的用户请求示例
chat_history = [
    {
        "role": "system",
        "content": sysprompt
    },
    {
        "role": "user",
        "content": "向前是正 X 轴方向(X增大代表飞行向前，减小代表飞行向后)。向右是正 Y 轴方向(Y增大代表飞行向右，减小代表飞行向左)。向下是正 Z 轴方向(Z增大代表飞行向下，减小代表飞行向上)。例如，要向前移动10个单位，向右移动20个单位，向上移动30个单位，应该表示为(x+10,y+20,z-30)。请向上移动 10 个单位"
    },
    {
        "role": "assistant",
        "content": """```python
aw.fly_to([aw.get_drone_position()[0], aw.get_drone_position()[1], aw.get_drone_position()[2]-10])
```

这段代码使用了 `fly_to()` 函数，将无人机移动到当前位置上方的 10 个单位。它通过调用 `get_drone_position()` 获取当前无人机的位置，然后创建一个新的列表，保持相同的 X 和 Y 坐标，但将 Z 坐标减少了 10。然后，无人机会通过 `fly_to()` 函数飞到这个新位置。"""
    }
]

# 定义一个函数，发送聊天请求给 DeepSeek
def ask(prompt):
    chat_history.append(
        {
            "role": "user",  # 用户提问
            "content": prompt,
        }
    )
    # 使用 DeepSeek API 进行交互
    completion = openai.ChatCompletion.create(
        model="deepseek-chat",  # 指定使用 DeepSeek 的聊天模型
        messages=chat_history,  # 传递聊天历史记录
        temperature=0  # 设置生成文本的多样性，0 表示生成更确定的响应
    )
    # 将助手的回复添加到聊天历史记录中
    chat_history.append(
        {
            "role": "assistant",  # 助手的回复
            "content": completion.choices[0].message.content,
        }
    )
    # 返回助手的最新回复
    return chat_history[-1]["content"]

# 正则表达式，用于提取代码块
code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)

# 定义一个函数，提取响应中的 Python 代码
def extract_python_code(content):
    code_blocks = code_block_regex.findall(content)  # 查找所有代码块
    if code_blocks:
        full_code = "\n".join(code_blocks)  # 将所有代码块拼接在一起

        # 如果代码块以 'python' 开头，去掉 'python' 字符串
        if full_code.startswith("python"):
            full_code = full_code[7:]

        return full_code
    else:
        return None  # 如果没有代码块，返回 None

# 定义颜色类，用于终端输出彩色文本
class colors:
    RED = "\033[31m"  # 红色
    ENDC = "\033[m"  # 结束符
    GREEN = "\033[32m"  # 绿色
    YELLOW = "\033[33m"  # 黄色
    BLUE = "\033[34m"  # 蓝色

# 初始化 AirSim 客户端
print(f"正在初始化 AirSim...")
aw = AirSimWrapper()  # 创建 AirSimWrapper 实例
print(f"完成.")

# 读取并发送启动提示信息
with open(args.prompt, "r", encoding="utf-8") as f:
    prompt = f.read()

ask(prompt)  # 发送初始提示
print("欢迎来到 AirSim 聊天机器人！我随时准备帮助你解答 AirSim 相关的问题和命令。")

# 进入命令行交互模式
while True:
    question = input(colors.YELLOW + "AirSim> " + colors.ENDC)  # 提示用户输入问题

    # 如果用户输入 '!quit' 或 '!exit'，则退出程序
    if question == "!quit" or question == "!exit":
        break

    # 如果用户输入 '!clear'，则清屏
    if question == "!clear":
        os.system("cls")
        continue

    # 否则，将用户问题传递给 DeepSeek 获取回答
    response = ask(question)

    print(f"\n{response}\n")  # 输出回答

    # 提取响应中的 Python 代码（如果有的话）
    code = extract_python_code(response)
    if code is not None:
        print("请稍等，我正在 AirSim 中运行代码...")
        exec(extract_python_code(response))  # 执行提取到的代码
        print("完成！\n")
