import streamlit as st
import json
import os
from openai import OpenAI

# ---------- 页面配置 ----------
st.set_page_config(page_title="工业质量 AI Agent", layout="centered")
st.title("🏭 工业质量 AI 助手")
st.caption("我可以帮你查询产品缺陷率、FMEA 分析建议，并生成完整的 FMEA 表格")

# ---------- 读取 API 密钥（支持本地 secrets 和云端环境变量）----------
try:
    API_KEY = st.secrets["DASHSCOPE_API_KEY"]
except Exception:
    API_KEY = os.environ.get("DASHSCOPE_API_KEY")
    if not API_KEY:
        st.error("❌ 未找到 API Key，请在 Streamlit Secrets 或环境变量中设置 DASHSCOPE_API_KEY")
        st.stop()

# ---------- 初始化 OpenAI 客户端（阿里云百炼兼容接口）----------
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ---------- 工具函数（模拟业务数据）----------
def query_defect_rate(product_code: str) -> str:
    """查询产品缺陷率"""
    data = {
        "A100": "划痕 1.2%，凹陷 0.3%",
        "B200": "气孔 0.5%，裂纹 0.1%",
        "C300": "无缺陷记录"
    }
    result = data.get(product_code, f"未找到产品 {product_code} 的数据，建议现场抽检")
    return f"产品 {product_code} 缺陷率：{result}"

def get_fmea_suggestions(process: str) -> str:
    """获取 FMEA 分析建议"""
    suggestions = {
        "冲压": "潜在失效模式：裂纹、毛刺。建议：定期更换模具（每5万次）、在线视觉检测、优化间隙。",
        "焊接": "潜在失效模式：气孔、未熔合。建议：参数实时监控、焊后超声波检查、定期校准设备。",
        "涂装": "潜在失效模式：流挂、色差。建议：温湿度控制、膜厚仪抽检、喷涂机器人轨迹优化。"
    }
    return suggestions.get(process, f"请提供具体工艺（冲压/焊接/涂装）")

def generate_fmea_table(process: str) -> str:
    """生成完整的 FMEA 表格（Markdown 格式）"""
    tables = {
        "冲压": """
| 功能 | 潜在失效模式 | 潜在失效影响 | 严重度(S) | 潜在原因 | 发生度(O) | 现行控制 | 探测度(D) | RPN | 建议措施 |
|------|--------------|--------------|-----------|----------|-----------|----------|-----------|-----|----------|
| 冲压成形 | 裂纹 | 零件强度不足 | 8 | 模具磨损、材料应力集中 | 4 | 目视抽检 | 6 | 192 | 定期换模、增加视觉检测 |
| 冲压成形 | 毛刺 | 后续装配干涉 | 6 | 刃口钝化、间隙不合理 | 5 | 去毛刺工序 | 4 | 120 | 优化间隙，高频修模 |
""",
        "焊接": """
| 功能 | 潜在失效模式 | 潜在失效影响 | 严重度(S) | 潜在原因 | 发生度(O) | 现行控制 | 探测度(D) | RPN | 建议措施 |
|------|--------------|--------------|-----------|----------|-----------|----------|-----------|-----|----------|
| 焊接连接 | 气孔 | 连接强度下降 | 7 | 保护气体不足、母材潮湿 | 3 | 破坏性抽检 | 5 | 105 | 增加气体流量传感器，烘干焊材 |
| 焊接连接 | 未熔合 | 开裂风险 | 9 | 焊接速度过快、电流不稳 | 2 | 超声波探伤 | 4 | 72 | 优化焊接参数，实时监控电流 |
""",
        "涂装": """
| 功能 | 潜在失效模式 | 潜在失效影响 | 严重度(S) | 潜在原因 | 发生度(O) | 现行控制 | 探测度(D) | RPN | 建议措施 |
|------|--------------|--------------|-----------|----------|-----------|----------|-----------|-----|----------|
| 表面涂层 | 流挂 | 外观不良 | 5 | 喷涂量过大、涂料粘度低 | 4 | 人工目检 | 3 | 60 | 自动喷涂参数闭环控制 |
| 表面涂层 | 色差 | 客户拒收 | 7 | 批次涂料差异、固化温度波动 | 3 | 色差仪抽检 | 2 | 42 | 加强来料检验，固化炉温度监控 |
"""
    }
    return tables.get(process, f"暂无 {process} 的完整表格，请提供工艺（冲压/焊接/涂装）")

# ---------- 工具描述（供大模型识别）----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_defect_rate",
            "description": "查询指定产品的缺陷率",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_code": {"type": "string", "description": "产品代码，如 A100, B200"}
                },
                "required": ["product_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fmea_suggestions",
            "description": "获取某个工艺的 FMEA 分析建议",
            "parameters": {
                "type": "object",
                "properties": {
                    "process": {"type": "string", "description": "工艺名称，如冲压、焊接、涂装"}
                },
                "required": ["process"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_fmea_table",
            "description": "生成指定工艺的完整 FMEA 表格（Markdown 格式）",
            "parameters": {
                "type": "object",
                "properties": {
                    "process": {"type": "string", "description": "工艺名称，如冲压、焊接、涂装"}
                },
                "required": ["process"]
            }
        }
    }
]

available_functions = {
    "query_defect_rate": query_defect_rate,
    "get_fmea_suggestions": get_fmea_suggestions,
    "generate_fmea_table": generate_fmea_table
}

# ---------- 初始化对话历史 ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个工业质量 AI Agent，可以根据用户的问题调用工具查询缺陷率、FMEA 建议或生成 FMEA 表格。回答要专业、简洁。"}
    ]

# 显示历史消息（不显示 system 和 tool 消息）
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ---------- 用户输入处理 ----------
if prompt := st.chat_input("试试问我：“A100的缺陷率”或“冲压工艺的 FMEA 分析”或“生成冲压的 FMEA 表格”"):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 构建 API 请求消息（排除 tool 角色消息，因为阿里云百炼不兼容）
    api_messages = [m for m in st.session_state.messages if m["role"] != "tool"]

    # 第一次调用模型，判断是否需要调用工具
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=api_messages,
        tools=tools,
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message

    # 处理工具调用
    if assistant_message.tool_calls:
        tool_call = assistant_message.tool_calls[0]
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)

        # 执行对应函数
        result = available_functions[func_name](**func_args)

        # 将模型的工具调用请求存入历史（但不能直接存对象，需转为字典）
        st.session_state.messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": func_name,
                        "arguments": tool_call.function.arguments
                    }
                }
            ]
        })

        # 添加工具返回结果
        st.session_state.messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

        # 第二次调用模型，将工具结果传入生成最终回答
        second_api_messages = [m for m in st.session_state.messages if m["role"] != "tool"]
        final_response = client.chat.completions.create(
            model="qwen-plus",
            messages=second_api_messages
        )
        final_answer = final_response.choices[0].message.content

        # 显示并保存最终回答
        with st.chat_message("assistant"):
            st.markdown(final_answer)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
    else:
        # 没有工具调用，直接回答
        answer = assistant_message.content
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})