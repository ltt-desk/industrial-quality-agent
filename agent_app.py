import streamlit as st
import json
from openai import OpenAI
API_KEY = st.secrets["DASHSCOPE_API_KEY"]

st.title("🏭 工业质量AI助手")
st.caption("我可以帮你查询产品缺陷率或进行FMEA分析")

# ------------------ 工具函数定义 ------------------
def query_defect_rate(product_code: str) -> str:
    data = {
        "A100": "划痕1.2%, 凹陷0.3%",
        "B200": "气孔0.5%, 裂纹0.1%"
    }
    return data.get(product_code, f"未找到 {product_code} 的数据，请现场抽检")

def get_fmea_suggestions(process: str) -> str:
    suggestions = {
        "冲压": "潜在失效模式：裂纹、毛刺。建议：定期换模具",
        "焊接": "潜在失效模式：气孔、未熔合。建议：参数监控"
    }
    return suggestions.get(process, f"请提供具体工艺（冲压/焊接）")

available_functions = {
    "query_defect_rate": query_defect_rate,
    "get_fmea_suggestions": get_fmea_suggestions
}

# ------------------ 工具描述（给AI看） ------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_defect_rate",
            "description": "查询指定产品的缺陷率数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_code": {"type": "string", "description": "产品代码，如A100"}
                },
                "required": ["product_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fmea_suggestions",
            "description": "获取某个工艺的FMEA分析建议",
            "parameters": {
                "type": "object",
                "properties": {
                    "process": {"type": "string", "description": "工艺名称，如冲压/焊接"}
                },
                "required": ["process"]
            }
        }
    }
]

# ------------------ 初始化OpenAI客户端 ------------------
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ------------------ 初始化聊天历史（统一用字典存储） ------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息（只显示 user 和 assistant，不显示 system 或 tool）
for msg in st.session_state.messages:
    role = msg.get("role")
    if role in ["user", "assistant"]:
        with st.chat_message(role):
            st.markdown(msg["content"])

# ------------------ 用户输入 ------------------
if prompt := st.chat_input("试试问我：“A100的缺陷率”或“冲压工艺的FMEA分析”"):
    # 保存用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用大模型（传入历史消息，注意历史消息里的 role 必须是 user/assistant/system，不能有 tool）
    # 注意：阿里云百炼的 API 不支持直接传 tool 角色的消息，需要特殊处理，但为了简化，我们只传 user+assistant
    api_messages = [m for m in st.session_state.messages if m.get("role") != "tool"]
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=api_messages,
        tools=tools,
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message
    # 处理 tool_calls
    if assistant_message.tool_calls:
        tool_call = assistant_message.tool_calls[0]
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)

        # 执行函数
        if func_name in available_functions:
            result = available_functions[func_name](**func_args)

            # 将 assistant 的“思考”存入历史（但注意 API 后续调用不需要 tool_calls 字段，我们存简化版）
            # 为了保持历史完整，我们把 assistant 的响应存为普通字典
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"（正在调用 {func_name} 查询...）"
            })
            # 再将工具结果作为一条 user 消息发给模型（一种简单方式）
            st.session_state.messages.append({
                "role": "user",
                "content": f"工具返回结果：{result}，请根据这个结果回答用户之前的问题：{prompt}"
            })

            # 重新调用模型，得到最终回答
            final_response = client.chat.completions.create(
                model="qwen-plus",
                messages=[{"role": "system", "content": "你是一个工业质量助手，基于工具返回的数据回答。"}] + st.session_state.messages[-2:]
            )
            final_answer = final_response.choices[0].message.content
            # 保存最终回答
            st.session_state.messages.append({"role": "assistant", "content": final_answer})
            with st.chat_message("assistant"):
                st.markdown(final_answer)
    else:
        # 没有 tool_calls，直接保存回答
        answer = assistant_message.content
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)