# ACE 框架 - 智能体上下文工程

基于 ACE (Agentic Context Engineering) 框架的 Python 实现，通过演进式上下文实现自我改进的大语言模型。

## 概述

ACE 框架将上下文视为动态演进的策略手册，而非静态提示。它通过生成、反思和策展的模块化过程，使大语言模型能够通过累积、提炼和组织策略来持续改进性能。
- Generator：作为 “执行者”，针对新查询生成完整推理轨迹（如 AppWorld 中的 API 调用代码、多步推理步骤），核心是暴露有效策略（如正确的分页逻辑）与反复出现的缺陷（如错误的身份识别方式）；
- Reflector：作为 “分析师”，基于执行反馈（如代码执行结果、测试报告）批判 Generator 的轨迹，提炼具体、可复用的洞察（如 “分页需用 while True 循环而非固定 range”），可选多轮迭代优化洞察质量，同时标记现有上下文条目的 “帮助 / 有害 / 中性” 标签；
- Curator：作为 “整合者”，将 Reflector 提炼的洞察合成为紧凑的 delta 条目（含结构化内容与元数据），通过轻量非 LLM 逻辑（如确定性合并规则）将 delta 条目融入现有上下文，同时执行语义嵌入去重，避免冗余。

### 核心特性

- **模块化架构**: 三个专门组件（执行者、分析师、整合者）协同工作
- **增量学习**: 通过结构化增量更新避免上下文崩溃
- **自我改进**: 从执行反馈中学习，无需标注监督
- **全面上下文**: 保留详细的领域知识而非压缩丢失
- **成本高效**: 平均降低 86.9% 的适应延迟

## 安装

```bash
# 克隆仓库
git clone <repository-url>
cd ace

# 安装依赖
pip install -e .

## 快速开始

```python
import asyncio
from ace import ACE
from ace.config_loader import get_ace_config

async def main():
    # 从配置文件加载配置
    config = get_ace_config()
    
    # 初始化 ACE
    ace = ACE(config)
    
    # 解决查询
    query = "编写一个计算数字阶乘的 Python 函数"
    trajectory, reflection = await ace.solve_query(query)
    
    print(f"成功: {trajectory.success}")
    print(f"生成的代码:\n{trajectory.generated_code}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 架构

### 组件

1. **执行者 (Generator)**: 使用当前策略手册生成推理轨迹
2. **分析师 (Reflector)**: 分析轨迹以提取见解和教训
3. **整合者 (Curator)**: 通过增量更新将见解整合到策略手册中

### 工作流程

```
查询 → 执行者 → 轨迹 → 分析师 → 反思 → 整合者 → 策略手册更新
```

## 核心概念

### 策略手册 (Playbook)

按章节组织的结构化知识点集合：
- **策略**: 通用方法和途径
- **错误模式**: 常见错误及避免方法
- **API 指南**: 特定 API 的最佳实践
- **验证检查清单**: 验证结果的步骤
- **公式**: 数学和计算公式

### 知识点 (Bullets)

具有以下特征的单个知识项：
- 内容和类型分类
- 有用/有害计数跟踪
- 章节组织
- 来源元数据

### 增量更新 (Delta Updates)

对策略手册的增量更改：
- 添加新见解而无需完全重写
- 根据使用情况更新知识点计数
- 去除重复并强制执行大小限制
- 保留现有知识

## 使用示例

### 基础查询解决

```python
# 单次查询，自动更新策略手册
trajectory, reflection = await ace.solve_query(
    "编写一个对数字列表进行排序的函数"
)
```

### 离线适应

```python
# 在数据集上训练
training_queries = [
    "编写一个检查数字是否为质数的函数",
    "创建一个查找列表中最大元素的函数",
    "编写一个反转字符串的函数"
]

stats = await ace.offline_adaptation(
    training_queries, 
    epochs=3
)
```

### 在线适应

```python
# 从执行反馈中适应
trajectory, reflection = await ace.online_adaptation(
    "处理这个数据文件",
    execution_feedback="函数执行失败，出现 TypeError"
)
```

### 性能评估

```python
# 评估而不更新策略手册
test_queries = ["测试查询 1", "测试查询 2"]
results = await ace.evaluate_performance(test_queries)
print(f"成功率: {results['success_rate']:.2%}")
```

## 配置

当前使用 ModelScope 的 Qwen3-32B 模型：

```yaml
# config.yaml
llm_provider:
  type: "custom"
  custom:
    base_url: "https://api-inference.modelscope.cn/v1"
    api_key: "your-api-key"
    default_model: "Qwen/Qwen3-32B"

models:
  generator:
    model: "Qwen/Qwen3-32B"
    temperature: 0.7
    max_tokens: 4096
  reflector:
    model: "Qwen/Qwen3-32B"
    temperature: 0.3
    max_tokens: 4096
  curator:
    model: "Qwen/Qwen3-32B"
    temperature: 0.2
    max_tokens: 4096
```

## 高级功能

### 自定义代码执行

```python
async def custom_executor(code: str) -> str:
    """自定义代码执行环境"""
    # 在此实现您的沙盒执行
    return "执行结果"

trajectory = await ace.generator.execute_trajectory(
    trajectory, 
    executor=custom_executor
)
```

### 策略手册管理

```python
# 保存策略手册
ace.save_playbook("my_playbook.json")

# 加载策略手册
ace.load_playbook("my_playbook.json")

# 重置策略手册
ace.reset_playbook()

# 获取摘要
summary = ace.get_playbook_summary()
print(f"总知识点数: {summary['total_bullets']}")
```

### 统计和监控

```python
# 获取框架统计信息
stats = ace.get_statistics()
print(f"成功率: {stats['success_rate']:.2%}")
print(f"总轨迹数: {stats['total_trajectories']}")
print(f"策略手册大小: {stats['playbook_size']}")
```

## 示例

查看 `examples/` 目录获取完整示例：

- `basic_usage.py`: 基础功能演示
- 更多示例即将推出...

## 测试

运行测试套件：

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_ace.py::TestACEFramework -v
```

## 运行演示

```bash
# 运行主程序演示
python main.py

# 运行快速演示
python run_example.py demo

# 运行基础示例
python run_example.py basic
```

## 研究背景

此实现基于张启正等人的论文 "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models" (2025)。

### 论文关键见解

1. **简洁性偏见**: 传统提示优化往往产生过于简洁的指令，丢失领域特定见解
2. **上下文崩溃**: 迭代重写可能导致知识被压缩掉，性能急剧下降
3. **演进式策略手册**: 将上下文视为全面的、演进式策略集合，保留详细知识

### 性能结果

- **智能体任务**: 相比强基线平均提升 10.6%
- **领域特定任务**: 平均提升 8.6%
- **成本降低**: 86.9% 更低的适应延迟
- **自我改进**: 无需标注监督即可有效工作

## 限制和注意事项

1. **API 成本**: 需要调用 LLM 提供商的 API
2. **质量依赖**: 性能取决于基础模型的质量
3. **反馈要求**: 在有可靠执行反馈或真实标签时效果最佳
4. **领域特异性**: 对知识密集型任务最为有益

## 贡献

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 为新功能添加测试
5. 提交拉取请求

## 联系方式
电子邮箱：yl_zhangqiang@foxmail.com

## 引用

如果您在研究中使用此框架，请引用原始论文：

```bibtex
@article{zhang2025agentic,
  title={Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models},
  author={Zhang, Qizheng and Hu, Changran and Upasani, Shubhangi and others},
  journal={arXiv preprint arXiv:2510.04618},
  year={2025}
}
```

---

**注意**: 这是 ACE 框架的独立实现，与原始作者无关。

## 当前状态

✅ **项目可以正常运行**
- 成功连接到 ModelScope API
- 配置加载正常
- LLM 客户端初始化成功
- 开始处理查询并生成响应

## 已修复的问题

1. **模型检测逻辑**: 修复了 LLM 客户端无法识别自定义提供商模型的问题
2. **思考模式兼容性**: 修复了 ModelScope API 在非流式调用中的兼容性问题