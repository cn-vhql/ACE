# ACE Framework Streamlit Dashboard

一个基于 Streamlit 的交互式 Web 界面，为 ACE 框架提供全面的管理和可视化功能。

## 🌟 功能特性

### 🏠 仪表盘概览
- **实时统计**: 显示成功率、总轨迹数、策略手册大小等关键指标
- **最近活动**: 查看最近的查询和执行历史
- **快速操作**: 一键重置策略手册、保存会话数据

### 💬 交互式问答界面
- **智能问答**: 输入查询，ACE 框架自动生成解决方案
- **实时执行**: 查看代码生成、执行结果和错误信息
- **推理分析**: 完整的推理步骤展示
- **反思洞察**: 深度分析和改进建议
- **高级选项**: 可调节温度、令牌限制等参数

### 📚 策略手册管理
- **可视化浏览**: 按类型、章节、标签筛选和浏览知识点
- **文件操作**: 上传、下载、导入、导出策略手册
- **统计分析**: 知识点分布图表和热力图
- **网络可视化**: 知识点关联关系图
- **实时更新**: 自动同步 ACE 框架的策略手册状态

### 📊 统计监控
- **性能趋势**: 成功率随时间变化图表
- **查询分析**: 查询长度、频率等详细分析
- **活动热力图**: 按小时显示查询活动
- **性能指标**: 综合性能数据可视化

### ⚙️ 配置管理
- **模型配置**: 查看当前使用的模型和参数
- **框架参数**: 调整反射轮数、训练轮次等设置
- **提供商信息**: API 配置和连接状态

### 🧪 批量处理
- **批量查询**: 一次处理多个查询
- **性能评估**: 在测试集上评估框架性能
- **结果导出**: 下载详细的评估报告

## 🚀 快速开始

### 环境要求

- Python 3.11+
- 已安装 ACE 框架依赖

### 安装可视化依赖

```bash
# 安装可视化库（可选，用于高级图表功能）
pip install plotly networkx pandas

# 或者使用项目的开发依赖
pip install -e .[dev]
```

### 启动应用

#### 方法 1: 使用启动脚本（推荐）

```bash
# 使用默认设置启动
python run_streamlit.py

# 指定端口启动
python run_streamlit.py --port 8080

# 启用调试模式
python run_streamlit.py --debug

# 查看帮助
python run_streamlit.py --help
```

#### 方法 2: 直接使用 Streamlit

```bash
# 基本启动
streamlit run streamlit_app.py

# 指定端口和主机
streamlit run streamlit_app.py --server.port 8080 --server.address 0.0.0.0
```

### 访问界面

启动后，在浏览器中访问：
- 本地：http://localhost:8501
- 或命令行中显示的地址

## 📖 使用指南

### 初次使用

1. **初始化框架**
   - 在侧边栏点击 "🚀 Initialize ACE Framework"
   - 等待初始化完成，看到 "✅ ACE Framework Ready" 提示

2. **开始问答**
   - 导航到 "💬 Q&A Interface" 页面
   - 输入查询，例如："写一个计算阶乘的 Python 函数"
   - 点击 "🚀 Solve" 按钮

3. **查看结果**
   - 查看生成的代码和执行结果
   - 浏览详细的推理步骤
   - 了解反思分析和改进建议

### 策略手册管理

1. **浏览知识点**
   - 进入 "📚 Playbook Manager" 页面
   - 使用筛选器按类型、章节、标签过滤
   - 点击展开查看详细内容

2. **可视化分析**
   - 点击 "🔥 Show Bullet Heatmap" 查看热力图
   - 点击 "🎯 Show Bullet Network" 查看关系网络
   - 分析知识点分布和关联

3. **文件操作**
   - 点击 "💾 Download Playbook" 下载当前策略手册
   - 点击 "📁 Upload Playbook" 上传已有的策略手册
   - 使用 "🔄 Reload from ACE" 同步框架状态

### 批量处理

1. **批量查询**
   - 进入 "🧪 Batch Processing" 页面
   - 输入多个查询（每行一个）
   - 设置训练轮次和更新选项
   - 点击 "🚀 Process Batch" 开始处理

2. **性能评估**
   - 输入测试查询
   - 点击 "🧪 Run Evaluation" 评估性能
   - 查看成功率等指标
   - 下载详细报告

## 🎨 界面组件

### 侧边栏控制面板

- **🎛️ Control Panel**: 主要控制选项
- **📡 Navigation**: 页面导航
- **⚡ Quick Actions**: 快速操作按钮

### 主要页面

1. **🏠 Dashboard**: 概览和最近活动
2. **💬 Q&A Interface**: 交互式问答
3. **📚 Playbook Manager**: 策略手册管理
4. **📊 Statistics**: 统计分析
5. **⚙️ Configuration**: 配置查看
6. **🧪 Batch Processing**: 批量处理

### 可视化功能

- **📈 性能图表**: 成功率趋势、查询分布等
- **🕸️ 网络图**: 知识点关联关系
- **🔥 热力图**: 知识点分布密度
- **📊 饼图/柱状图**: 统计数据展示

## 🔧 故障排除

### 常见问题

1. **依赖缺失错误**
   ```
   ImportError: No module named 'plotly'
   ```
   **解决方案**:
   ```bash
   pip install plotly networkx pandas
   ```

2. **配置文件错误**
   ```
   Failed to load configuration
   ```
   **解决方案**: 确保 `config.yaml` 文件存在且格式正确

3. **API 连接失败**
   ```
   Failed to initialize ACE Framework
   ```
   **解决方案**: 检查 API 密钥和网络连接

4. **端口占用**
   ```
   Port 8501 is already in use
   ```
   **解决方案**:
   ```bash
   python run_streamlit.py --port 8081
   ```

### 调试模式

启用调试模式获取详细错误信息：

```bash
python run_streamlit.py --debug
```

### 检查应用状态

运行测试脚本验证应用状态：

```bash
python test_streamlit.py
```

## 📁 文件结构

```
ACE/
├── streamlit_app.py           # 主应用文件
├── run_streamlit.py          # 启动脚本
├── test_streamlit.py         # 测试脚本
├── ace/
│   ├── streamlit_utils.py    # 可视化工具函数
│   └── ...
├── config.yaml               # 配置文件
└── STREAMLIT_README.md       # 本文档
```

## 🎯 使用技巧

### 1. 优化查询效果
- 使用具体的查询描述
- 在高级选项中调整参数
- 查看推理步骤了解处理过程

### 2. 策略手册管理
- 定期下载备份策略手册
- 使用标签系统组织知识点
- 通过可视化分析知识覆盖度

### 3. 批量处理
- 将相关查询分组处理
- 使用较小的批次大小避免超时
- 监控性能指标调整参数

### 4. 性能监控
- 定期查看统计页面
- 关注成功率趋势
- 根据查询分析优化使用模式

## 🔒 安全注意事项

- **API 密钥安全**: 不要在代码中硬编码 API 密钥
- **代码执行**: ACE 框架会执行生成的代码，请在安全环境中使用
- **数据隐私**: 注意处理查询时的数据隐私问题

## 🚀 高级功能

### 自定义可视化

开发者可以扩展 `ace/streamlit_utils.py` 添加自定义可视化函数：

```python
def create_custom_visualization(data):
    """创建自定义可视化"""
    # 使用 plotly 创建图表
    fig = px.bar(...)
    return fig
```

### 扩展页面功能

在 `streamlit_app.py` 中添加新页面：

```python
def render_custom_page():
    """渲染自定义页面"""
    st.header("🎯 Custom Page")
    # 添加页面内容
```

然后在导航菜单中添加选项。

## 📞 技术支持

如遇到问题，请：

1. 查看控制台错误信息
2. 运行 `python test_streamlit.py` 诊断问题
3. 检查 `config.yaml` 配置
4. 查阅 ACE 框架主文档

## 🔄 更新日志

### v1.0.0
- ✅ 完整的 Streamlit 界面
- ✅ 策略手册管理功能
- ✅ 交互式问答界面
- ✅ 统计分析和可视化
- ✅ 批量处理功能
- ✅ 配置管理界面
- ✅ 依赖检查和错误处理

---

**注意**: 本界面是 ACE 框架的 Web 前端，核心功能由 ACE 框架提供。界面需要与正确的配置和 API 连接配合使用。