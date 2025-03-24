#cmp_chatgpt_airsim.py
import openai  # 导入 OpenAI API 交互库
import re  # 正则表达式库，用于提取 Python 代码块
import argparse  # 解析命令行参数
from airsim_wrapper import *  # 导入 AirSim 控制封装类
import math  # 数学库
import numpy as np  # NumPy 计算库
import os  # 操作系统交互库（如清屏等）
import json  # 处理 JSON 配置文件
import time  # 计时模块
import csv  # 处理 CSV 文件

# ========================== 1. 解析命令行参数 ==========================
parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="prompts/airsim_basic.txt")  # 任务提示词文件
parser.add_argument("--sysprompt", type=str, default="system_prompts/airsim_basic.txt")  # 系统提示词文件
parser.add_argument("--repeat", type=int, default=3, help="每个任务的重复实验次数")  # 设定实验重复次数
args = parser.parse_args()

# ========================== 2. 读取 API Key ==========================
with open("config.json", "r") as f:
    config = json.load(f)  # 读取配置文件中的 API Key

openai.api_key = config["OPENAI_API_KEY"]  # 设置 OpenAI API Key


# ========================== 3. 定义 ChatGPT 交互函数 ==========================
def ask(prompt, chat_history):
    """
    发送请求到 ChatGPT，并返回响应内容和响应时间
    :param prompt: 任务指令
    :param chat_history: 当前对话的历史记录
    :return: ChatGPT 生成的回复文本，及响应时间（秒）
    """
    chat_history.append({"role": "user", "content": prompt})

    start_time = time.time()  # 记录请求开始时间
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # 使用 GPT-4o Mini 模型
        messages=chat_history,  # 传递聊天记录
        temperature=0  # 设定温度，0 代表输出更确定
    )
    response_time = round(time.time() - start_time, 2)  # 计算响应时间
    response = completion.choices[0].message.content  # 获取 LLM 生成的文本

    chat_history.append({"role": "assistant", "content": response})  # 记录助手的回复
    return response, response_time


# ========================== 4. 提取 Python 代码块 ==========================
def extract_python_code(content):
    """
    从文本中提取 Python 代码
    :param content: ChatGPT 生成的文本
    :return: 代码字符串（如果存在），否则返回 None
    """
    code_blocks = re.findall(r"```python\s+(.*?)```", content, re.DOTALL)  # 识别 Python 代码块
    return "\n".join(code_blocks) if code_blocks else None  # 返回代码或 None


# ========================== 5. 初始化 AirSim ==========================
print("初始化 AirSim...")
aw = AirSimWrapper()  # 创建 AirSim 客户端
print("AirSim 初始化完成。")

# ========================== 6. 设定实验数据文件 ==========================
csv_filename = "chatgpt_experiment_results.csv"


# 记录实验数据
def log_experiment(data):
    """
    记录实验数据到 CSV 文件
    :param data: 需要写入的行数据（列表格式）
    """
    file_exists = os.path.isfile(csv_filename)  # 检查文件是否已存在
    with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["任务类型", "模型", "实验次数", "生成代码", "代码执行状态", "任务完成状态", "响应时间(s)"])
        writer.writerow(data)


# ========================== 7. 定义实验任务 ==========================
tasks = {
    "基础任务": "请让无人机起飞，然后降落。",
    "单点导航": "请飞向涡轮机2，并在沿 X 轴负方向保持 12 米距离，高度达到 50 米。",
    "路径规划": "请让无人机绕塔 tower3 → tower2 → tower1 巡航, 高度 50 米，并与塔沿 X 轴负方向保持 10 米距离。",
    "复杂飞行": """太阳能面板阵列的前后宽度为30米，左右长度为50米。
    假设通过 aw.get_position("solarpanels") 获取到太阳能面板的坐标 (x, y, z)，
    则阵列的四个端点分别是：(x, y, z), (x-30, y, z), (x-30, y-50, z), (x, y-50, z)。
    你需要让无人机按照以下算法扫描整个面板阵列，无人机的扫描算法如下：
    1. 无人机从阵列的最右前端顶点 (x, y, z) 起飞，并保持飞行高度为5米。
    2. 将阵列的长度（50米）均分为10行。
    3. 在每次飞行过程中，无人机沿阵列的宽度方向（即从前到后）逐行扫描，每次飞行完成后，
       飞往下一行的起点，准备扫描下一行。（即：沿x方向从x到x-30）
    4. 重复此过程，直到覆盖整个太阳能面板阵列。"""
}

# ========================== 8. 执行实验 ==========================
for task_name, task_prompt in tasks.items():
    execution_times = []  # 记录所有实验的响应时间
    success_count = 0  # 记录成功执行的次数
    print(f"\n🔹 正在执行任务: {task_name}")

    for i in range(args.repeat):
        print(f"🔸 第 {i + 1}/{args.repeat} 次实验")

        # 每次实验前，重新加载系统提示和基础提示词，并重置 chat_history
        with open(args.sysprompt, "r", encoding="utf-8") as f:
            sysprompt = f.read()
        with open(args.prompt, "r", encoding="utf-8") as f:
            basic_prompt = f.read()

        chat_history = [
            {"role": "system", "content": sysprompt},
            {"role": "user", "content": basic_prompt}
        ]

        # 发送任务指令
        response, response_time = ask(task_prompt, chat_history)
        code = extract_python_code(response)
        execution_status = "✅"
        completion_status = "✅"

        if code:
            try:
                exec(code, {"aw": aw, "airsim": airsim, "np": np, "math": math})  # 执行代码
                success_count += 1
            except Exception as e:
                print(f"⚠ 执行失败: {e}")
                execution_status = completion_status = "❌"
        else:
            print("⚠ 未检测到 Python 代码！")
            execution_status = completion_status = "❌"

        # 记录实验数据
        log_experiment([task_name, "ChatGPT", f"{i + 1}/{args.repeat}", code or "无代码",
                        execution_status, completion_status, response_time])
        execution_times.append(response_time)

        # 让无人机返回初始位置
        print("🔹 无人机返回初始位置 (0,0,0) 并降落...")
        aw.fly_to([0, 0, 0])
        aw.land()
        print("🔹 无人机已重置。\n")

    # 计算并记录平均数据
    avg_response_time = round(np.mean(execution_times), 2)
    success_rate = round((success_count / args.repeat) * 100, 2)
    avg_summary = f"平均响应时间: {avg_response_time}s | 成功率: {success_rate}%"

    log_experiment([task_name, "ChatGPT", "平均值", avg_summary, "-", "-", avg_response_time])

print("\n🚀 ChatGPT实验完成，所有结果已保存至 chatgpt_experiment_results.csv。\n")