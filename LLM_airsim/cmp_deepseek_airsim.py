#cmp_deepseek_airsim.py
import openai              # DeepSeek API 交互库
import re                  # 正则表达式库，用于提取Python代码
import argparse            # 命令行参数解析库
from airsim_wrapper import *  # AirSim 封装类，用于控制无人机
import math                # 数学库
import numpy as np         # NumPy计算库，用于统计
import os                  # 操作系统交互库
import json                # JSON文件读写库
import time                # 时间库，用于计算响应时间
import csv                 # CSV文件操作库，用于记录实验数据

# ================== 1. 解析命令行参数 ==================
parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="prompts/airsim_basic.txt")  # 基础提示词路径
parser.add_argument("--sysprompt", type=str, default="system_prompts/airsim_basic.txt")  # 系统提示词路径
parser.add_argument("--repeat", type=int, default=3, help="每个任务的重复实验次数")  # 每个任务重复次数
args = parser.parse_args()

# ================== 2. 读取 DeepSeek API Key ==================
with open("config.json", "r") as f:
    config = json.load(f)

openai.api_key = config["DEEPSEEK_API_KEY"]    # 设置DeepSeek API密钥
openai.api_base = "https://api.deepseek.com"   # 设置DeepSeek API基础URL

# ================== 3. 定义 DeepSeek 交互函数 ==================
def ask(prompt, chat_history):
    """
    向DeepSeek发送提示，并返回响应内容和响应时间
    """
    chat_history.append({"role": "user", "content": prompt})
    start_time = time.time()  # 请求开始计时

    # 调用DeepSeek API获取响应
    completion = openai.ChatCompletion.create(
        model="deepseek-chat",
        messages=chat_history,
        temperature=0
    )

    response_time = round(time.time() - start_time, 2)  # 计算响应耗时
    response = completion.choices[0].message.content  # 提取返回内容

    chat_history.append({"role": "assistant", "content": response})  # 更新聊天记录
    return response, response_time

# ================== 4. 提取 Python 代码块函数 ==================
def extract_python_code(content):
    """
    提取文本中的 Python 代码块
    """
    code_blocks = re.findall(r"```python\s+(.*?)```", content, re.DOTALL)
    return "\n".join(code_blocks) if code_blocks else None

# ================== 5. 初始化 AirSim 客户端 ==================
print("初始化 AirSim...")
aw = AirSimWrapper()  # 创建AirSim控制对象
print("AirSim 初始化完成。")

# ================== 6. 设定实验数据记录文件 ==================
csv_filename = "deepseek_experiment_results.csv"

def log_experiment(data):
    """
    将实验数据记录到CSV文件
    """
    file_exists = os.path.isfile(csv_filename)
    with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["任务类型", "模型", "实验次数", "生成代码", "代码执行状态", "任务完成状态", "响应时间(s)"])
        writer.writerow(data)

# ================== 7. 定义实验任务 ==================
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

# ================== 8. 执行实验流程 ==================
for task_name, task_prompt in tasks.items():
    execution_times = []  # 存储每次实验的响应时间
    success_count = 0     # 成功完成任务的次数统计
    print(f"\n🔹 正在执行任务: {task_name}")

    for i in range(args.repeat):
        print(f"🔸 第 {i+1}/{args.repeat} 次实验")

        # 每次实验开始前重新加载并初始化聊天记录
        with open(args.sysprompt, "r", encoding="utf-8") as f:
            sysprompt = f.read()
        with open(args.prompt, "r", encoding="utf-8") as f:
            basic_prompt = f.read()

        chat_history = [
            {"role": "system", "content": sysprompt},
            {"role": "user", "content": basic_prompt}
        ]

        # 向DeepSeek发送任务指令
        response, response_time = ask(task_prompt, chat_history)
        code = extract_python_code(response)  # 提取返回代码
        execution_status = "✅"
        completion_status = "✅"

        if code:
            try:
                # 执行生成的代码
                exec(code, {"aw": aw, "airsim": airsim, "np": np, "math": math})
                success_count += 1
            except Exception as e:
                print(f"⚠ 执行失败: {e}")
                execution_status = completion_status = "❌"
        else:
            print("⚠ 未检测到 Python 代码！")
            execution_status = completion_status = "❌"

        # 记录本次实验数据
        log_experiment([task_name, "DeepSeek", f"{i+1}/{args.repeat}", code or "无代码",
                        execution_status, completion_status, response_time])

        execution_times.append(response_time)

        # 实验结束后让无人机返回原点(0,0,0)并降落
        print("🔹 无人机返回初始位置 (0,0,0) 并降落...")
        aw.fly_to([0, 0, 0])
        aw.land()
        print("🔹 无人机已重置。\n")

    # 计算并记录实验的平均响应时间和成功率
    avg_response_time = round(np.mean(execution_times), 2)
    success_rate = round((success_count / args.repeat) * 100, 2)
    avg_summary = f"平均响应时间: {avg_response_time}s | 成功率: {success_rate}%"

    # 将平均数据记录到CSV文件
    log_experiment([task_name, "DeepSeek", "平均值", avg_summary, "-", "-", avg_response_time])

# ================== 实验完成提示 ==================
print("\n🚀 DeepSeek实验完成，所有结果已保存至 deepseek_experiment_results.csv。\n")
