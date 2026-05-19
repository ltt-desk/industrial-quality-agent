# 🏭 工业质量 AI Agent

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://industrial-quality-agent.streamlit.app)

本项目是一个面向制造业质量管理的 **AI Agent 原型**，基于大语言模型（通义千问）和工具调用（Function Calling）技术，能够理解自然语言问题，自动查询产品缺陷率、检索 FMEA 分析建议，并以对话形式提供专业回答。

> 该作品为个人的实践项目，展示 Agent 核心能力：规划、记忆、工具使用。

---

## ✨ 功能演示

| 用户提问 | Agent 动作 | 回答示例 |
|---------|-----------|----------|
| “A100 的缺陷率” | 调用 `query_defect_rate` 工具 | “产品 A100 缺陷率：划痕1.2%，凹陷0.3%，总计1.5%。” |
| “冲压工艺的 FMEA 分析” | 调用 `get_fmea_suggestions` 工具 | “冲压工艺潜在失效模式：裂纹、毛刺。建议：定期更换模具、在线视觉检测。” |
| “B200 有没有缺陷数据？” | 调用工具 + 自然语言生成 | “B200 产品缺陷率为气孔0.5%，裂纹0.1%。” |

- **多轮对话**：保留上下文，支持追问。
- **自主决策**：Agent 自动判断是否需要调用工具，无需用户手动指定。

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| 大模型 | 阿里云百炼（通义千问 qwen-plus） |
| Agent 范式 | OpenAI Function Calling（兼容接口） |
| Web 界面 | Streamlit |
| 部署平台 | Streamlit Community Cloud |
| 语言环境 | Python 3.8+ |

---

## 🚀 在线体验

无需安装，直接访问云端部署版本：

🔗 **[https://industrial-quality-agent.streamlit.app](https://industrial-quality-agent.streamlit.app)**

> 提示：首次加载可能需几秒，请耐心等待。支持手机/电脑访问。

---

## 📦 本地运行（开发者）

如果你想在本地修改或学习代码，请按以下步骤操作。

### 1. 克隆仓库

```bash
git clone https://github.com/ltt-desk/industrial-quality-agent.git
cd industrial-quality-agent

### 2. 安装依赖
pip install -r requirements.txt

### 3. 配置 API 密钥
注册 阿里云百炼 并开通服务。

在控制台创建 API Key（以 sk- 开头）。

在项目根目录创建文件夹 .streamlit，并在其中创建文件 secrets.toml，内容如下：
DASHSCOPE_API_KEY = "sk-你的真实密钥"
⚠️ 切勿将 secrets.toml 提交到 Git（已在 .gitignore 中忽略）。

4. 启动应用
streamlit run agent_app.py
浏览器自动打开 http://localhost:8501，即可开始对话。

📁 项目结构
industrial-quality-agent/
├── agent_app.py              # 主程序：Agent 逻辑 + Streamlit UI
├── requirements.txt          # Python 依赖
├── .streamlit/
│   └── secrets.toml          # 本地密钥（不入库）
└── README.md                 # 项目说明

🧠 Agent 设计细节
工具定义（Tools）
使用 OpenAI 兼容的 Function Calling 格式声明两个工具：
1. query_defect_rate
◦ 描述：查询指定产品的缺陷率
◦ 参数：product_code (string)
2. get_fmea_suggestions
◦ 描述：获取某个工艺的 FMEA 分析建议
◦ 参数：process (string)

调用流程

用户输入 → 大模型（带 tools 参数）→ 判断是否需要工具
   ↓ 需要调用
执行对应 Python 函数 → 将结果返回模型 → 生成最终自然语言回答
   ↓ 不需要调用
直接返回模型回答

记忆机制

• 使用 st.session_state.messages 存储对话历史（字典列表）。
• 每次请求将最近的消息发送给模型，实现上下文记忆。

📄 License
本项目为个人作品，仅用于展示技术能力。数据均为模拟，不涉及商业机密。
MIT License.
￼
👩‍💻 作者
ltt
• 🔗 GitHub：https://github.com/ltt-desk

🙏 致谢
• 阿里云百炼提供的免费大模型算力
• Streamlit 团队提供的低代码 Web 框架

📌 后续改进方向
• 接入真实数据库（PostgreSQL / MySQL）替代模拟数据
• 增加更多质检工具（如 query_inspection_record, get_defect_image）
• 使用 LangGraph 实现多步规划（例如：先查缺陷率，再推荐改善措施）
• 集成可视化图表（Streamlit 原生图表展示缺陷趋势）



