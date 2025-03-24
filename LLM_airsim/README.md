# 基于大模型的无人机任务规划

## 项目简介

本项目旨在利用大型语言模型（LLM）实现无人机任务规划与控制，通过自然语言交互，自动生成并执行无人机飞行任务。项目使用了 **AirSim** 仿真平台进行任务模拟，通过整合 **ChatGPT（GPT-4o Mini）**、**DeepSeek** 和 **Ollama（DeepSeek-R1:1.5b 本地模型）** 三个大模型，以便进行对比实验分析各大模型在无人机任务规划中的性能表现。

---

## 目录结构

```
├── airsim_wrapper.py              # 封装 AirSim API，提供无人机基本控制接口
├── AnythingLLM_airsim.py          # 连接 AnythingLLM 本地知识库
├── chatgpt_airsim.py              # 连接 ChatGPT 模型进行任务规划
├── deepseek_airsim.py             # 连接 DeepSeek 模型进行任务规划
├── ollama_airsim.py               # 连接本地 Ollama DeepSeek-R1:1.5b 模型
├── cmp_chatgpt_airsim.py          # ChatGPT 模型对比实验脚本
├── cmp_deepseek_airsim.py         # DeepSeek 模型对比实验脚本
├── prompts
│   └── airsim_basic.txt           # 基础提示词（用户输入任务指令示例）
├── system_prompts
│   └── airsim_basic.txt           # 系统提示词（模型交互规范约束）
├── environment.yml                # 项目环境配置文件（conda 环境）
├── config.json                    # 存放模型 API Key 的配置文件
└── README.md                      # 项目说明文档（本文件）
```

---

## 项目运行环境配置

本项目使用 **Anaconda** 和 **PyCharm** 进行开发，并在 **Windows 10** 系统下测试通过。

### 1. 前提条件

- 已安装 **Anaconda**
- 已安装 **AirSim**
- 已获得 **DeepSeek** 和 **ChatGPT** 的 API 密钥

### 2. 项目环境安装

在项目根目录下执行以下命令创建环境：

```shell
conda env create -f environment.yml
conda activate chatgpt
pip install airsim
```

### 3. 配置 API 密钥

请在项目根目录的 `config.json` 文件中填写你的 API 密钥：

```json
{
  "DEEPSEEK_API_KEY": "你的 DeepSeek API 密钥",
  "OPENAI_API_KEY": "你的 ChatGPT API 密钥"
}
```

### 4. 启动 AirSim 模拟器

- 从此处下载 `AirSimInspection.zip` [Releases](https://github.com/microsoft/PromptCraft-Robotics/releases)，并解压 `AirSimInspection.zip` 文件。
- 复制`settings.json`到`AirSimInspection` 文件夹。
- 进入 `AirSimInspection` 文件夹，运行 `run.bat` 以启动 AirSim 仿真环境。

---

## 项目运行方法

### 单模型交互模式

确保 AirSim 环境已启动后，打开命令行终端，执行以下任意脚本进入交互模式：

- 使用 **ChatGPT**：

```shell
python chatgpt_airsim.py
```

- 使用 **DeepSeek**：

```shell
python deepseek_airsim.py
```

- 使用 **Ollama 本地模型**：

```shell
python ollama_airsim.py
```

此时，你可以在终端的 `AirSim>` 提示符后输入自然语言指令，程序会自动调用对应的模型生成并执行任务代码。

例如：

```shell
AirSim> 请飞向 turbine2 并保持12米距离，高度50米。
```

### 对比实验模式

分别运行以下脚本来执行针对不同大模型的对比实验：

- **ChatGPT 对比实验**：

```shell
python cmp_chatgpt_airsim.py
```

- **DeepSeek 对比实验**：

```shell
python cmp_deepseek_airsim.py
```

实验完成后，会在根目录生成相应的 CSV 文件：

- `chatgpt_experiment_results.csv`
- `deepseek_experiment_results.csv`

记录了每次实验任务的响应时间、成功率、生成代码及执行情况。

---

## 支持的无人机控制函数

项目通过封装 AirSim API 提供以下标准函数：

- `aw.takeoff()` - 无人机起飞
- `aw.land()` - 无人机降落
- `aw.get_drone_position()` - 获取无人机当前位置 (X,Y,Z)
- `aw.fly_to([x, y, z])` - 飞向目标坐标
- `aw.fly_path(points)` - 沿指定路径飞行
- `aw.set_yaw(yaw)` - 设置偏航角
- `aw.get_yaw()` - 获取当前偏航角
- `aw.get_position(object_name)` - 获取指定物体的位置

---

## 场景中的可用物体

项目使用的 AirSim 仿真环境中存在以下预定义物体：

- **风力涡轮机**: `turbine1`, `turbine2`
- **太阳能面板**: `solarpanels`
- **汽车**: `car`
- **人群**: `crowd`
- **电塔**: `tower1`, `tower2`, `tower3`

---

## 坐标轴定义

- 向前为正 X 轴方向 (`x`增大代表飞行向前，减小代表飞行向后)
- 向右为正 Y 轴方向 (`y`增大代表飞行向右，减小代表飞行向左)
- 向下为正 Z 轴方向 (`z`增大代表飞行向下，减小代表飞行向上)

例如，向前移动 10 米，向右移动 20 米，向上移动 30 米，应表示为 `(x+10, y+20, z-30)`。

---

## 更多信息与文档

- [AirSim 官方文档](https://microsoft.github.io/AirSim/)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs)
- [PromptCraft-Robotics](https://github.com/microsoft/PromptCraft-Robotics)
---

## 联系作者

如果有任何问题或改进建议，请联系项目作者。

---

🚀 **项目搭建完毕，欢迎使用！**
