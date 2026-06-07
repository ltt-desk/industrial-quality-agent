# 🏭 工业质量 AI Agent

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://industrial-quality-agent.streamlit.app)

面向制造业质量管理的 **全功能 AI Agent**，基于通义千问大模型和 Function Calling 技术，覆盖来料检验、过程控制、成品检测、客诉处理全流程，支持多 Agent 协作、缺陷图片智能分析、质量数据可视化看板和自动报告生成。

> 个人实践项目，展示 AI Agent 核心能力：**感知 → 规划 → 工具使用 → 记忆 → 多Agent协作**

---

## ✨ 功能全景

### 💬 智能助手
- 自然语言质量问答，自动调用 10 个业务工具
- 内嵌质量管理知识库（ISO 9001 / FMEA / SPC / 8D / 5-Why / QC七大手法）
- 知识库模式一键切换

### 🤖 多 Agent 协作
- **Orchestrator** 调度 → 5 个专业 Agent 并行分析 → 首席质量官综合报告
- 来料检验(IQC) · 过程控制(IPQC) · 成品检测(OQC) · 客诉处理 · 数据分析
- 6 种预设分析场景 + 自定义问题

### 📊 数据看板
- KPI 指标卡：综合良率、缺陷数、CPK 均值、客诉关闭率
- 缺陷趋势折线图 + 帕累托图 + 严重度分布
- 🔴 **实时监控模式**：模拟产线状态 + 异常告警

### 📋 报告中心
- 日报 / 周报 / 月报 / 8D客诉报告一键生成
- Markdown + TXT 双格式下载

### 📸 缺陷图片分析
- 上传/拍摄产品缺陷照片 → qwen-vl-max 多模态识别
- 自动输出：缺陷类型、严重度、原因分析、改善建议

### 🔗 质量全链路追溯
- 输入批次号 → 来料 → 过程 → 成品 → 出货 → 客诉全链路可视化
- 一键生成追溯报告

### ⚖️ 供应商评分看板
- 8 家供应商质量绩效排名
- 月度评分趋势 + 各维度对比 + AI 评估

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| 大模型 | 阿里云百炼 — qwen-plus / qwen-vl-max |
| Agent 范式 | OpenAI Function Calling（兼容接口） |
| Web 框架 | Streamlit |
| 数据 | 仿真生成（5产品 × 180天 × 5工艺） |
| 部署 | Streamlit Community Cloud |
| 语言 | Python 3.10+ |

---

## 🚀 在线体验

🔗 **[industrial-quality-agent.streamlit.app](https://industrial-quality-agent.streamlit.app)**

> 首次加载约需 10 秒，支持 PC / 手机访问。

---

## 📦 本地运行

### 1. 克隆仓库

```bash
git clone https://github.com/ltt-desk/industrial-quality-agent.git
cd industrial-quality-agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥

注册 [阿里云百炼](https://bailian.console.aliyun.com/) 并开通 qwen-plus 和 qwen-vl-max 服务。

在项目根目录创建 `.streamlit/secrets.toml`：

```toml
DASHSCOPE_API_KEY = "sk-你的真实密钥"
```

> ⚠️ `secrets.toml` 已在 `.gitignore` 中排除，不会被提交到 Git。

### 4. 启动应用

```bash
streamlit run agent_app.py
```

浏览器自动打开 `http://localhost:8501`。

---

## 📁 项目结构

```
industrial-quality-agent/
├── agent_app.py          # 主程序（1643行）：7 Tab + 全部业务逻辑
├── requirements.txt      # Python 依赖
├── .gitignore            # 排除密钥和缓存文件
└── README.md
```

---

## 🧠 Agent 架构

### 工具层（10 个 Function Calling 工具）

| 工具 | 功能 |
|------|------|
| `query_defect_rate` | 查询产品缺陷率及趋势 |
| `get_fmea_suggestions` | 获取工艺 FMEA 分析建议 |
| `generate_fmea_table` | 生成完整 FMEA 表格（含 RPN） |
| `query_incoming_inspection` | 查询来料检验数据 |
| `query_process_quality` | 查询过程 Cpk 等质量参数 |
| `query_final_inspection` | 查询成品检验合格率 |
| `query_complaints` | 查询客户投诉记录 |
| `query_knowledge` | 检索质量管理知识库 |
| `trace_batch` | 批次全链路追溯 |
| `query_supplier_score` | 供应商评分与排名 |

### 调用流程

```
用户输入 → 单次 API 调用（带 tools + 详细 System Prompt）
  ├── 无需工具 → 千问原生质量直接回答（与官网体验一致）
  └── 需要工具 → 执行 Python 函数 → 第二轮纯聊天模式生成回答
```

### 多 Agent 协作流程

```
用户问题 → Orchestrator 规划任务
                ↓
    ┌──────────┼──────────┬──────────┐
    ↓          ↓          ↓          ↓
  IQC        IPQC       OQC       Complaint    Analysis
  Agent      Agent      Agent     Agent        Agent
    └──────────┼──────────┴──────────┘
               ↓
        Synthesis Agent（首席质量官）
               ↓
          综合质量分析报告
```

---

## 📊 数据说明

所有质量数据为**仿真生成**（固定随机种子保证一致性），仅供演示：

- **检验记录**：5 产品 × 180 天 = 900 条
- **缺陷明细**：500 条（含缺陷类型、严重度、关联工艺）
- **客诉记录**：80 条（含客户、损失金额）
- **批次追溯**：A100/B200/C300 各 10 批次
- **供应商**：8 家 × 6 个月评分记录

---

## 📄 License

MIT License. 本项目为个人作品，数据均为模拟，不涉及商业机密。

---

## 👩‍💻 作者

**ltt** — [GitHub](https://github.com/ltt-desk)

---

## 🙏 致谢

- 阿里云百炼 — 通义千问 API
- Streamlit — 低代码 Web 框架
