import streamlit as st
import json
import os
import re
import random
import time
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
from openai import OpenAI

# =============================================================================
# 页面配置
# =============================================================================
st.set_page_config(
    page_title="工业质量 AI Agent",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 配置层
# =============================================================================
try:
    API_KEY = st.secrets["DASHSCOPE_API_KEY"]
except Exception:
    API_KEY = os.environ.get("DASHSCOPE_API_KEY")
    if not API_KEY:
        st.error("❌ 未找到 API Key，请在 Streamlit Secrets 或环境变量中设置 DASHSCOPE_API_KEY")
        st.stop()

client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

MODEL_NAME = "qwen-plus"  # 默认稳定模型，侧边栏可切换到 qwen-max


# =============================================================================
# 数据仿真层
# =============================================================================
random.seed(42)  # 固定种子确保演示一致性

PRODUCTS = {
    "A100": "冲压件-车身侧围",
    "B200": "焊接总成-底盘",
    "C300": "涂装件-引擎盖",
    "D400": "装配总成-车门",
    "E500": "精密铸件-变速箱壳体",
}

PROCESSES = ["冲压", "焊接", "涂装", "装配", "铸造"]
DEFECT_TYPES = ["划痕", "气孔", "裂纹", "毛刺", "色差", "尺寸偏差", "变形", "锈蚀", "硬度不足", "装配不良"]
SEVERITY_LEVELS = ["轻微", "中等", "严重", "致命"]
CUSTOMERS = ["比亚迪", "上汽", "吉利", "奇瑞", "长城", "蔚来", "理想", "小鹏"]

def generate_inspection_records(n_days=180):
    """生成每日检验记录"""
    records = []
    start_date = datetime.now() - timedelta(days=n_days)
    for i in range(n_days):
        date = start_date + timedelta(days=i)
        for product_code, product_name in PRODUCTS.items():
            total = random.randint(200, 1000)
            defect_count = int(random.gauss(15, 8))
            defect_count = max(0, min(defect_count, total))
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "product_code": product_code,
                "product_name": product_name,
                "total_inspected": total,
                "defect_count": defect_count,
                "defect_rate": round(defect_count / total * 100, 2),
            })
    return records

def generate_defect_details(records, n_defects=500):
    """生成缺陷明细"""
    details = []
    for _ in range(n_defects):
        rec = random.choice(records)
        defect_type = random.choices(
            DEFECT_TYPES,
            weights=[15, 10, 8, 12, 7, 20, 5, 3, 8, 12],
            k=1
        )[0]
        details.append({
            "date": rec["date"],
            "product_code": rec["product_code"],
            "product_name": rec["product_name"],
            "defect_type": defect_type,
            "severity": random.choices(SEVERITY_LEVELS, weights=[3, 5, 1.5, 0.5], k=1)[0],
            "process": random.choice(PROCESSES),
            "quantity": random.randint(1, 20),
        })
    return details

def generate_process_cpk():
    """生成过程能力指数"""
    return {p: round(random.gauss(1.33, 0.15), 2) for p in PROCESSES}

def generate_complaints(n=80):
    """生成客户投诉记录"""
    complaints = []
    statuses = ["已关闭", "处理中", "待确认", "已关闭", "已关闭"]  # 偏重已关闭
    for _ in range(n):
        days_ago = random.randint(1, 180)
        date = datetime.now() - timedelta(days=days_ago)
        product_code = random.choice(list(PRODUCTS.keys()))
        defect = random.choice(DEFECT_TYPES)
        complaints.append({
            "date": date.strftime("%Y-%m-%d"),
            "customer": random.choice(CUSTOMERS),
            "product_code": product_code,
            "product_name": PRODUCTS[product_code],
            "issue": f"{defect}超标，影响装配精度",
            "severity": random.choices(SEVERITY_LEVELS, weights=[1, 3, 4, 2], k=1)[0],
            "status": random.choice(statuses),
            "cost": random.randint(5000, 200000),
        })
    return complaints

@st.cache_data
def load_all_data():
    """加载/生成所有仿真数据（缓存避免每次刷新重新生成）"""
    records = generate_inspection_records(180)
    return {
        "inspection_records": records,
        "defect_details": generate_defect_details(records, 500),
        "process_cpk": generate_process_cpk(),
        "complaints": generate_complaints(80),
    }

data = load_all_data()

# ---------- 供应商数据仿真 ----------
SUPPLIERS = {
    "宝钢": {"products": ["A100", "D400"], "type": "钢材"},
    "鞍钢": {"products": ["A100", "E500"], "type": "钢材"},
    "巴斯夫": {"products": ["C300"], "type": "涂料"},
    "PPG": {"products": ["C300"], "type": "涂料"},
    "博世": {"products": ["B200", "D400"], "type": "电子"},
    "大陆": {"products": ["B200"], "type": "电子"},
    "海拉": {"products": ["D400"], "type": "车灯"},
    "延锋": {"products": ["D400", "E500"], "type": "内饰"},
}

def generate_supplier_scores():
    """生成供应商月度评分数据"""
    scores = {}
    for name, info in SUPPLIERS.items():
        base_q = random.uniform(85, 99)
        base_d = random.uniform(80, 98)
        monthly = []
        for m in range(6):
            monthly.append({
                "month": (datetime.now() - timedelta(days=30 * (5 - m))).strftime("%Y-%m"),
                "quality_rate": round(base_q + random.uniform(-5, 3), 1),
                "delivery_rate": round(base_d + random.uniform(-8, 2), 1),
                "complaints": random.randint(0, 5),
                "cost": random.randint(5000, 80000),
            })
        latest = monthly[-1]
        overall = round(
            latest["quality_rate"] * 0.4
            + latest["delivery_rate"] * 0.3
            + max(0, 100 - latest["complaints"] * 3) * 0.2
            + max(0, 100 - latest["cost"] / 1000) * 0.1,
            1
        )
        scores[name] = {"info": info, "monthly": monthly, "overall": overall}
    return scores

# ---------- 批次追溯数据仿真 ----------
def generate_batch_traces():
    """为每个产品生成批次追溯数据"""
    traces = {}
    for product_code in ["A100", "B200", "C300"]:
        product_traces = []
        for i in range(10):
            batch_date = datetime.now() - timedelta(days=random.randint(5, 170))
            batch_id = f"LOT-{product_code}-{batch_date.strftime('%Y%m%d')}-{i+1:03d}"
            supplier_name = random.choice([s for s, info in SUPPLIERS.items() if product_code in info["products"]])
            process_steps = []
            if product_code == "A100":
                process_steps = [("冲压", "Cpk=1.38 ✅"), ("去毛刺", "合格")]
            elif product_code == "B200":
                process_steps = [("焊接", "Cpk=1.25 ⚠️"), ("探伤", "合格"), ("打磨", "合格")]
            elif product_code == "C300":
                process_steps = [("前处理", "合格"), ("喷涂", "Cpk=1.42 ✅"), ("固化", "温度±2°C ✅")]

            shipped = batch_date + timedelta(days=random.randint(3, 10))
            inspection_result = random.choices(["合格", "让步接收", "退货"], weights=[8, 1.5, 0.5], k=1)[0]
            has_complaint = random.random() < 0.15

            product_traces.append({
                "batch_id": batch_id,
                "product_code": product_code,
                "product_name": PRODUCTS[product_code],
                "batch_date": batch_date.strftime("%Y-%m-%d"),
                "quantity": random.randint(500, 5000),
                "supplier": supplier_name,
                "incoming_inspection": {
                    "result": inspection_result,
                    "defect_rate": round(random.uniform(0.1, 3.0), 2),
                    "inspector": f"QC-{random.randint(100, 999)}",
                },
                "process_steps": process_steps,
                "final_inspection": {
                    "total": random.randint(200, 800),
                    "defects": random.randint(0, 15),
                    "result": "合格" if random.random() < 0.9 else "让步接收",
                },
                "shipping": {
                    "date": shipped.strftime("%Y-%m-%d"),
                    "customer": random.choice(CUSTOMERS),
                    "quantity": random.randint(300, 4000),
                },
                "complaint": {
                    "has_complaint": has_complaint,
                    "issue": f"{random.choice(DEFECT_TYPES)}问题" if has_complaint else None,
                    "cost": random.randint(5000, 50000) if has_complaint else 0,
                }
            })
        traces[product_code] = product_traces
    return traces

supplier_scores = generate_supplier_scores()
batch_traces = generate_batch_traces()

# =============================================================================
# 知识库层
# =============================================================================
QUALITY_KNOWLEDGE = {
    "ISO 9001": {
        "title": "ISO 9001:2015 质量管理体系",
        "content": """
**ISO 9001:2015 核心要求：**

1. **以客户为关注焦点**：理解并满足客户要求，超越客户期望
2. **领导作用**：建立统一的质量方针和目标，创造全员参与的环境
3. **全员参与**：确保所有层级人员都具备能力、被授权并积极参与
4. **过程方法**：将活动作为相互关联的过程系统进行管理
5. **改进**：成功的组织持续关注改进
6. **循证决策**：基于数据和信息的分析和评估做出决策
7. **关系管理**：管理与供方等相关方的关系

**关键条款：**
- 第4章 组织环境：理解组织及其环境、相关方需求
- 第5章 领导作用：质量方针、组织角色与职责
- 第6章 策划：应对风险和机遇的措施、质量目标
- 第7章 支持：资源、能力、意识、沟通、文件化信息
- 第8章 运行：运行策划和控制、产品和服务要求
- 第9章 绩效评价：监视测量分析评价、内部审核、管理评审
- 第10章 改进：不合格与纠正措施、持续改进
"""
    },
    "FMEA": {
        "title": "FMEA 失效模式与影响分析（AIAG VDA 第5版）",
        "content": """
**FMEA 七步法：**

1. **策划与准备**：确定分析范围、组建跨职能团队
2. **结构分析**：识别过程步骤、功能与要求
3. **功能分析**：描述每个步骤的功能和潜在失效
4. **失效分析**：识别失效模式、失效影响、失效原因
5. **风险分析**：评估严重度(S)、发生度(O)、探测度(D)
6. **优化**：确定行动优先级(AP)，制定改进措施
7. **结果文件化**：记录分析结果和措施跟踪

**风险评分（1-10）：**
- 严重度(S)：失效影响的严重程度
- 发生度(O)：失效原因发生的概率
- 探测度(D)：现有控制探测到失效的能力

**RPN = S × O × D**

**行动优先级(AP)替代RPN阈值：**
- 高优先级(H)：必须采取改进措施
- 中优先级(M)：建议采取改进措施
- 低优先级(L)：维持现有控制
"""
    },
    "SPC": {
        "title": "SPC 统计过程控制",
        "content": """
**SPC 核心概念：**

1. **普通原因变异**：过程固有的、稳定的变异来源
2. **特殊原因变异**：异常的外部因素导致的变异，需要调查和消除

**常用控制图：**
- Xbar-R 图：均值和极差控制图
- Xbar-S 图：均值和标准差控制图
- P 图：不合格品率控制图
- NP 图：不合格品数控制图
- C 图：缺陷数控制图
- U 图：单位缺陷数控制图

**过程能力指数：**
- Cp = (USL - LSL) / (6σ)：过程潜在能力
- Cpk = min[(USL-μ)/(3σ), (μ-LSL)/(3σ)]：过程实际能力
- Cpk ≥ 1.33：过程能力充足
- 1.0 ≤ Cpk < 1.33：过程能力一般
- Cpk < 1.0：过程能力不足

**判异准则（8大规则）：**
1点超出3σ界限 | 连续9点在中心线同侧 | 连续6点递增/递减 | 连续14点交替上下
"""
    },
    "8D": {
        "title": "8D 问题解决法",
        "content": """
**8D 八步法（G8D）：**

- **D0**：准备过程 — 评估是否需要启动8D
- **D1**：建立团队 — 组建跨职能小组，明确角色
- **D2**：描述问题 — 用5W2H清晰定义问题（What, Who, Where, When, Why, How, How many）
- **D3**：临时遏制措施 — 保护客户不受问题影响
- **D4**：根本原因分析 — 使用鱼骨图、5-Why 等方法找出根因
- **D5**：选择永久纠正措施 — 验证措施有效性
- **D6**：实施永久纠正措施 — 全面推行并监控
- **D7**：防止再发 — 标准化、FMEA更新、经验教训
- **D8**：团队庆祝 — 认可团队贡献，知识分享

**关键工具：**
- IS/IS NOT 分析表
- 鱼骨图（人机料法环）
- 5-Why 分析法
- 验证计划（DOE等）
"""
    },
    "5Why": {
        "title": "5-Why 根因分析法",
        "content": """
**5-Why 分析步骤：**

1. 明确问题现象
2. 问第一个"为什么"→ 找到直接原因
3. 问第二个"为什么"→ 深入一层
4. 持续追问，直到找到系统性的根本原因
5. 制定对策（针对根本原因，而非表象）

**注意事项：**
- 每个"为什么"的回答必须是事实，不是猜测
- 避免跳到结论，保持逻辑链条
- 可能需要多于或少于5个为什么
- 最终要追溯到一个可以采取行动的系统性问题
- 多人参与，避免个人偏见

**示例（产品表面划痕）：**
1. 为什么有划痕？→ 模具表面有磨损
2. 为什么模具有磨损？→ 超过更换周期未更换
3. 为什么超期未换？→ 没有模具寿命监控机制
4. 为什么没有监控？→ 缺少预防性维护制度
5. 为什么缺少制度？→ 设备管理流程不完善
→ 根因：设备管理体系不健全
"""
    },
    "QC工具": {
        "title": "QC 七大手法",
        "content": """
**QC 七大手法的应用：**

1. **检查表**：系统化收集数据，确保数据完整准确
2. **层别法**：按来源/时间/工序分层分析，找出差异
3. **柏拉图（帕累托图）**：80/20法则，聚焦主要问题
4. **特性要因图（鱼骨图）**：从人机料法环五个维度找原因
5. **直方图**：展示数据分布，判断过程能力
6. **散布图**：分析两个变量间的相关性
7. **控制图**：区分普通原因和特殊原因变异

**使用建议：**
- 问题分析：鱼骨图 + 5-Why
- 优先级排序：帕累托图
- 过程监控：控制图 + 直方图
- 数据收集：检查表 + 层别法
"""
    },
}

def search_quality_knowledge(query: str, top_k: int = 3) -> str:
    """简单关键词匹配检索质量知识库"""
    query_lower = query.lower()
    scored = {}
    for key, entry in QUALITY_KNOWLEDGE.items():
        score = 0
        title_lower = entry["title"].lower()
        content_lower = entry["content"].lower()
        keywords_map = {
            "iso": key == "ISO 9001",
            "9001": key == "ISO 9001",
            "质量体系": key == "ISO 9001",
            "质量管理体系": key == "ISO 9001",
            "fmea": key == "FMEA",
            "失效模式": key == "FMEA",
            "失效影响": key == "FMEA",
            "rpn": key == "FMEA",
            "spc": key == "SPC",
            "统计过程": key == "SPC",
            "控制图": key == "SPC",
            "cpk": key == "SPC",
            "过程能力": key == "SPC",
            "8d": key == "8D",
            "八步法": key == "8D",
            "问题解决": key == "8D",
            "纠正措施": key == "8D",
            "5why": key == "5Why",
            "5-why": key == "5Why",
            "五问法": key == "5Why",
            "根本原因": key == "5Why",
            "根因": key == "5Why",
            "鱼骨图": key == "QC工具",
            "帕累托": key == "QC工具",
            "柏拉图": key == "QC工具",
            "qc手法": key == "QC工具",
            "七大手法": key == "QC工具",
        }
        for kw, matches_key in keywords_map.items():
            if kw in query_lower and matches_key:
                score += 10
        for word in query_lower.replace("，", " ").replace("。", " ").split():
            if word in title_lower:
                score += 3
            if word in content_lower:
                score += 1
        if score > 0:
            scored[key] = score
    sorted_keys = sorted(scored, key=scored.get, reverse=True)[:top_k]
    if not sorted_keys:
        return "未找到相关知识条目，请尝试更具体的查询。"
    results = []
    for key in sorted_keys:
        entry = QUALITY_KNOWLEDGE[key]
        results.append(f"### {entry['title']}\n{entry['content']}")
    return "\n\n---\n\n".join(results)

# =============================================================================
# 工具函数层
# =============================================================================
def query_defect_rate(product_code: str) -> str:
    """查询产品缺陷率"""
    recs = [r for r in data["inspection_records"] if r["product_code"] == product_code]
    if not recs:
        return f"未找到产品 {product_code} 的数据，建议现场抽检。"
    recent = recs[-30:]
    avg_rate = round(sum(r["defect_rate"] for r in recent) / len(recent), 2)
    trend = "上升" if recent[-1]["defect_rate"] > recent[0]["defect_rate"] else "下降"
    details = [r for r in data["defect_details"] if r["product_code"] == product_code]
    type_dist = Counter(d["defect_type"] for d in details).most_common(5)
    type_str = "、".join(f"{t}({c}次)" for t, c in type_dist)
    return (
        f"产品 {product_code}（{PRODUCTS[product_code]}）\n"
        f"近30天平均缺陷率：{avg_rate}%\n"
        f"趋势：{trend}\n"
        f"主要缺陷类型：{type_str}"
    )

def get_fmea_suggestions(process: str) -> str:
    """获取 FMEA 分析建议"""
    suggestions = {
        "冲压": "潜在失效模式：裂纹、毛刺、变形。建议：定期更换模具（每5万次）、在线视觉检测、优化冲压间隙。",
        "焊接": "潜在失效模式：气孔、未熔合、裂纹。建议：参数实时监控、焊后超声波检查、定期校准设备。",
        "涂装": "潜在失效模式：流挂、色差、附着力不足。建议：温湿度控制、膜厚仪抽检、喷涂机器人轨迹优化。",
        "装配": "潜在失效模式：错装、漏装、扭矩不足。建议：防错夹具、力矩自动监控、装配顺序防呆。",
        "铸造": "潜在失效模式：缩孔、夹杂、冷隔。建议：浇注温度控制、模具预热、X光在线检测。",
    }
    return suggestions.get(process, f"请提供具体工艺（{'/'.join(PROCESSES)}）")

def generate_fmea_table(process: str) -> str:
    """生成 FMEA 表格"""
    tables = {
        "冲压": """
| 功能 | 潜在失效模式 | 潜在失效影响 | S | 潜在原因 | O | 现行控制 | D | RPN | 建议措施 |
|------|-------------|-------------|---|---------|---|---------|---|-----|---------|
| 冲压成形 | 裂纹 | 零件强度不足 | 8 | 模具磨损、材料应力集中 | 4 | 目视抽检 | 6 | 192 | 换模周期优化、视觉检测 |
| 冲压成形 | 毛刺 | 装配干涉 | 6 | 刃口钝化、间隙不合理 | 5 | 去毛刺工序 | 4 | 120 | 模具间隙优化、高频修模 |
| 冲压落料 | 尺寸偏差 | 无法装配 | 7 | 定位不准、板材滑移 | 3 | 首件检验 | 5 | 105 | 激光定位、伺服送料 |
""",
        "焊接": """
| 功能 | 潜在失效模式 | 潜在失效影响 | S | 潜在原因 | O | 现行控制 | D | RPN | 建议措施 |
|------|-------------|-------------|---|---------|---|---------|---|-----|---------|
| 焊接连接 | 气孔 | 连接强度下降 | 7 | 保护气体不足、母材潮湿 | 3 | 破坏性抽检 | 5 | 105 | 增加气体流量传感器，烘干焊材 |
| 焊接连接 | 未熔合 | 开裂风险 | 9 | 焊接速度过快、电流不稳 | 2 | 超声波探伤 | 4 | 72 | 优化焊接参数、实时电流监控 |
| 焊接定位 | 错位 | 尺寸不合格 | 6 | 夹具磨损、定位松动 | 3 | 通止规检查 | 4 | 72 | 定期校准夹具、位置传感器 |
""",
        "涂装": """
| 功能 | 潜在失效模式 | 潜在失效影响 | S | 潜在原因 | O | 现行控制 | D | RPN | 建议措施 |
|------|-------------|-------------|---|---------|---|---------|---|-----|---------|
| 表面涂层 | 流挂 | 外观不良 | 5 | 喷涂量过大、涂料粘度低 | 4 | 人工目检 | 3 | 60 | 自动喷涂参数闭环控制 |
| 表面涂层 | 色差 | 客户拒收 | 7 | 涂料批次差异、固化温度波动 | 3 | 色差仪抽检 | 2 | 42 | 来料检验加严、烘炉温度监控 |
| 前处理 | 附着力不足 | 涂层脱落 | 8 | 除油不净、磷化不良 | 2 | 划格法抽检 | 4 | 64 | 前处理药液自动补加系统 |
""",
        "装配": """
| 功能 | 潜在失效模式 | 潜在失效影响 | S | 潜在原因 | O | 现行控制 | D | RPN | 建议措施 |
|------|-------------|-------------|---|---------|---|---------|---|-----|---------|
| 螺栓拧紧 | 扭矩不足 | 松动异响 | 7 | 气动扳手未校准 | 3 | 抽检扭矩 | 5 | 105 | 电动定扭工具+数据记录 |
| 卡扣连接 | 未卡到位 | 脱落风险 | 8 | 操作疲劳、节拍过快 | 4 | 手感确认 | 6 | 192 | 到位传感器自动检测 |
| 线束插接 | 插针弯曲 | 电路失效 | 9 | 盲插操作、无导向 | 2 | 通电测试 | 4 | 72 | 导向结构优化、CCD视觉检查 |
""",
        "铸造": """
| 功能 | 潜在失效模式 | 潜在失效影响 | S | 潜在原因 | O | 现行控制 | D | RPN | 建议措施 |
|------|-------------|-------------|---|---------|---|---------|---|-----|---------|
| 浇注成形 | 缩孔 | 强度降低 | 8 | 浇注温度偏高、补缩不足 | 3 | X光抽检 | 5 | 120 | 优化浇注系统、增加冒口 |
| 型腔填充 | 冷隔 | 表面缺陷 | 6 | 浇注速度慢、模具温度低 | 3 | 外观全检 | 4 | 72 | 预热模具、提高浇注速度 |
| 砂芯成形 | 夹砂 | 内部孔洞 | 7 | 砂芯强度不足 | 2 | 超声波检测 | 4 | 56 | 砂芯树脂比例优化 |
""",
    }
    return tables.get(process, f"暂无 {process} 的完整FMEA表格，请从 {'/'.join(PROCESSES)} 中选择。")

def query_incoming_inspection(product_code: str) -> str:
    """查询来料检验数据"""
    recs = [r for r in data["inspection_records"] if r["product_code"] == product_code]
    if not recs:
        return f"未找到产品 {product_code} 的来料检验数据。"
    recent = recs[-10:]
    avg_rate = round(sum(r["defect_rate"] for r in recent) / len(recent), 2)
    return (
        f"产品 {product_code} 近10批来料检验情况：\n"
        f"平均不良率：{avg_rate}%\n"
        f"最近批次：{recent[-1]['date']}，不良率 {recent[-1]['defect_rate']}%\n"
        f"判定：{'⚠️ 需加严检验' if avg_rate > 2.0 else '✅ 可正常检验'}"
    )

def query_process_quality(process: str) -> str:
    """查询过程质量数据"""
    if process not in PROCESSES:
        return f"未找到工艺 {process} 的数据。可选：{'/'.join(PROCESSES)}"
    cpk = data["process_cpk"].get(process, 0)
    if cpk >= 1.33:
        level = "✅ 能力充足"
    elif cpk >= 1.0:
        level = "⚠️ 能力一般，需关注"
    else:
        level = "❌ 能力不足，需立即改善"
    details = [d for d in data["defect_details"] if d["process"] == process]
    type_dist = Counter(d["defect_type"] for d in details).most_common(5)
    return (
        f"工艺 {process} 过程质量概况：\n"
        f"Cpk = {cpk}（{level}）\n"
        f"主要缺陷：{', '.join(f'{t}({c}次)' for t, c in type_dist)}"
    )

def query_final_inspection(product_code: str) -> str:
    """查询成品检验数据"""
    recs = [r for r in data["inspection_records"] if r["product_code"] == product_code]
    if not recs:
        return f"未找到产品 {product_code} 的成品检验数据。"
    recent = recs[-30:]
    avg_rate = round(sum(r["defect_rate"] for r in recent) / len(recent), 2)
    pass_rate = round(100 - avg_rate, 2)
    return (
        f"产品 {product_code} 近30天成品检验：\n"
        f"总检验数：{sum(r['total_inspected'] for r in recent)}\n"
        f"合格率：{pass_rate}%\n"
        f"不良率：{avg_rate}%"
    )

def query_complaints(product_code: str = None) -> str:
    """查询客诉记录"""
    complaints = data["complaints"]
    if product_code:
        complaints = [c for c in complaints if c["product_code"] == product_code]
    if not complaints:
        return f"暂无{'产品 ' + product_code + ' 的' if product_code else ''}客诉记录。"
    recent = sorted(complaints, key=lambda x: x["date"], reverse=True)[:10]
    lines = [f"最近 {len(recent)} 条客诉记录："]
    for c in recent:
        lines.append(f"- [{c['date']}] {c['customer']} | {c['product_code']} | {c['issue']} | 状态：{c['status']} | 损失：¥{c['cost']:,}")
    return "\n".join(lines)

def query_knowledge(topic: str) -> str:
    """检索质量管理知识"""
    return search_quality_knowledge(topic)

def trace_batch(batch_id: str) -> str:
    """根据批次号追溯全链路质量数据"""
    for product_code, traces in batch_traces.items():
        for t in traces:
            if t["batch_id"] == batch_id:
                steps_text = "\n".join(
                    f"  {i+1}. {step[0]}：{step[1]}"
                    for i, step in enumerate(t["process_steps"])
                )
                complaint_text = (
                    f"⚠️ 有客诉：{t['complaint']['issue']}，损失 ¥{t['complaint']['cost']:,}"
                    if t["complaint"]["has_complaint"]
                    else "✅ 无客诉"
                )
                return (
                    f"批次号：{t['batch_id']}\n"
                    f"产品：{t['product_name']}（{t['product_code']}）\n"
                    f"生产日期：{t['batch_date']} | 数量：{t['quantity']}\n\n"
                    f"📥 来料检验：{t['incoming_inspection']['result']} "
                    f"（不良率 {t['incoming_inspection']['defect_rate']}%）\n"
                    f"供应商：{t['supplier']}\n\n"
                    f"⚙️ 过程参数：\n{steps_text}\n\n"
                    f"📤 成品检验：{t['final_inspection']['total']}件检验，"
                    f"{t['final_inspection']['defects']}件不良，"
                    f"判定：{t['final_inspection']['result']}\n\n"
                    f"🚚 出货：{t['shipping']['date']} → {t['shipping']['customer']} "
                    f"（{t['shipping']['quantity']}件）\n\n"
                    f"📋 客诉：{complaint_text}"
                )
    # 模糊搜索
    available = []
    for pc, traces in batch_traces.items():
        for t in traces[:3]:
            available.append(t["batch_id"])
    return f"未找到批次 {batch_id}。可查询的批次示例：{', '.join(available[:6])}..."

def query_supplier_score(supplier_name: str = None) -> str:
    """查询供应商评分"""
    if supplier_name and supplier_name not in supplier_scores:
        return f"未找到供应商 {supplier_name}。可选：{'、'.join(supplier_scores.keys())}"
    if supplier_name:
        s = supplier_scores[supplier_name]
        monthly_str = "\n".join(
            f"  {m['month']}：质量 {m['quality_rate']}% | 交付 {m['delivery_rate']}% | 客诉 {m['complaints']}次 | 质量成本 ¥{m['cost']:,}"
            for m in s["monthly"][-3:]
        )
        return (
            f"供应商：{supplier_name}（{s['info']['type']}）\n"
            f"综合评分：{s['overall']}/100\n"
            f"供货产品：{'、'.join(s['info']['products'])}\n\n"
            f"近3个月表现：\n{monthly_str}"
        )
    # 排名
    ranked = sorted(supplier_scores.items(), key=lambda x: x[1]["overall"], reverse=True)
    lines = [f"{'排名':<6}{'供应商':<8}{'评分':<8}{'类型'}" ]
    for i, (name, s) in enumerate(ranked, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        lines.append(f"{emoji:<6}{name:<8}{s['overall']:<8}{s['info']['type']}")
    return "\n".join(lines)

def analyze_defect_image(image_base64: str, user_description: str = "") -> str:
    """
    调用 qwen-vl-max 多模态模型分析缺陷图片。
    通过 HTTP 请求 DashScope 原生 API（兼容 OpenAI 格式）。
    """
    import base64
    import urllib.request
    import urllib.error

    prompt_text = (
        "你是一位资深的工业质量检测专家。请分析这张产品缺陷照片，按以下格式输出：\n"
        "1. **缺陷类型**：判断缺陷类别（划痕/气孔/裂纹/毛刺/色差/变形/锈蚀/其他）\n"
        "2. **严重度评级**：轻微/中等/严重/致命，并给出理由\n"
        "3. **可能原因**：从人机料法环角度分析最可能的2-3个原因\n"
        "4. **改善建议**：给出具体可操作的改善措施（短期+长期）\n"
        "5. **是否需要立即停机**：是/否，并说明判断依据"
    )
    if user_description:
        prompt_text = f"用户补充说明：{user_description}\n\n{prompt_text}"

    payload = {
        "model": "qwen-vl-max",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                ],
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }

    req = urllib.request.Request(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return f"❌ 图片分析API调用失败 (HTTP {e.code})：{error_body[:500]}"
    except Exception as e:
        return f"❌ 图片分析请求异常：{str(e)[:500]}"

# =============================================================================
# 工具注册
# =============================================================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_defect_rate",
            "description": "查询指定产品的缺陷率数据",
            "parameters": {"type": "object", "properties": {"product_code": {"type": "string", "description": "产品代码"}}, "required": ["product_code"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fmea_suggestions",
            "description": "获取某个工艺的FMEA分析建议",
            "parameters": {"type": "object", "properties": {"process": {"type": "string", "description": "工艺名称"}}, "required": ["process"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_fmea_table",
            "description": "生成指定工艺的完整FMEA表格",
            "parameters": {"type": "object", "properties": {"process": {"type": "string", "description": "工艺名称"}}, "required": ["process"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_incoming_inspection",
            "description": "查询产品的来料检验数据",
            "parameters": {"type": "object", "properties": {"product_code": {"type": "string", "description": "产品代码"}}, "required": ["product_code"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_process_quality",
            "description": "查询工艺过程质量数据（Cpk等）",
            "parameters": {"type": "object", "properties": {"process": {"type": "string", "description": "工艺名称"}}, "required": ["process"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_final_inspection",
            "description": "查询产品成品检验数据",
            "parameters": {"type": "object", "properties": {"product_code": {"type": "string", "description": "产品代码"}}, "required": ["product_code"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_complaints",
            "description": "查询客户投诉记录，可指定产品代码或查全部",
            "parameters": {"type": "object", "properties": {"product_code": {"type": "string", "description": "产品代码（可选）"}}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_knowledge",
            "description": "检索质量管理知识库（ISO/FMEA/SPC/8D等）",
            "parameters": {"type": "object", "properties": {"topic": {"type": "string", "description": "检索主题"}}, "required": ["topic"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trace_batch",
            "description": "根据批次号追溯全链路质量数据（来料→过程→成品→出货→客诉）",
            "parameters": {"type": "object", "properties": {"batch_id": {"type": "string", "description": "批次号，如 LOT-A100-20240601-001"}}, "required": ["batch_id"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_supplier_score",
            "description": "查询供应商质量评分和绩效排名",
            "parameters": {"type": "object", "properties": {"supplier_name": {"type": "string", "description": "供应商名称（可选，不填则返回排名）"}}}
        }
    },
]

available_functions = {
    "query_defect_rate": query_defect_rate,
    "get_fmea_suggestions": get_fmea_suggestions,
    "generate_fmea_table": generate_fmea_table,
    "query_incoming_inspection": query_incoming_inspection,
    "query_process_quality": query_process_quality,
    "query_final_inspection": query_final_inspection,
    "query_complaints": query_complaints,
    "query_knowledge": query_knowledge,
    "trace_batch": trace_batch,
    "query_supplier_score": query_supplier_score,
}

# =============================================================================
# System Prompts
# =============================================================================
CHAT_SYSTEM = (
    "你是通义千问，一个专业的工业质量管理 AI 助手。\n\n"
    "你有权调用以下工具来获取实时数据：\n"
    "- query_defect_rate：查询产品缺陷率\n"
    "- query_incoming_inspection：查询来料检验数据\n"
    "- query_process_quality：查询过程质量数据（Cpk等）\n"
    "- query_final_inspection：查询成品检验数据\n"
    "- query_complaints：查询客诉记录\n"
    "- get_fmea_suggestions：获取FMEA分析建议\n"
    "- generate_fmea_table：生成FMEA表格\n"
    "- trace_batch：根据批次号追溯全链路质量数据\n"
    "- query_supplier_score：查询供应商评分\n"
    "- query_knowledge：检索质量管理知识库\n\n"
    "当用户询问具体产品/工艺/批次的数据时，请主动调用相应工具获取最新数据。\n"
    "当用户咨询质量管理知识时，调用 query_knowledge 检索知识库。\n"
    "如果可以基于你的专业知识直接回答，则直接回答。\n\n"
    "回答风格要求：\n"
    "- 专业、详尽、全面，像质量管理专家一样深入分析\n"
    "- 对工具返回的数据要深入解读，结合行业最佳实践给出洞见\n"
    "- 善用结构化格式（标题、列表、表格、分段）使回答清晰易读\n"
    "- 主动提供延伸知识和改善建议\n"
    "- 回答要充分展开，不要过于简短"
)

KNOWLEDGE_CHAT_SYSTEM = (
    "你是通义千问，一个精通质量管理体系的 AI 专家。\n\n"
    "你可以调用 query_knowledge 工具检索质量管理知识库，也可以调用其他质量数据工具。\n\n"
    "当用户询问质量管理标准/方法论时，请调用 query_knowledge，\n"
    "并结合检索结果给出专业、详尽的解读和实际应用指导。\n\n"
    "回答风格：专业、权威、全面、深入，像质量管理专家授课一样。"
)

# Multi-Agent System Prompts
ORCHESTRATOR_PROMPT = (
    "你是质量管理总调度师。分析用户的质量问题，制定分析计划，"
    "确定需要哪些专业Agent参与分析。输出JSON格式：\n"
    '{"summary": "问题概述", "required_agents": ["IQC","IPQC","OQC","Complaint","Analysis"], "analysis_plan": "分析步骤"}'
)

IQC_AGENT_PROMPT = (
    "你是来料检验(IQC)专家。专注于分析来料质量数据，"
    "评估供应商质量表现，识别来料异常趋势。"
    "根据数据判断是否需加严检验或供应商整改。"
)

IPQC_AGENT_PROMPT = (
    "你是过程控制(IPQC)专家。专注于过程参数监控和Cpk分析，"
    "识别过程变异来源，评估过程稳定性。"
    "给出参数优化和过程改进建议。"
)

OQC_AGENT_PROMPT = (
    "你是成品检测(OQC)专家。专注于成品质量数据分析，"
    "评估出货质量风险，识别系统性缺陷模式。"
    "给出拦截方案和出货质量保证建议。"
)

COMPLAINT_AGENT_PROMPT = (
    "你是客诉质量(CQS)专家。专注于客户投诉分析，"
    "识别客诉规律和重大质量风险，估算质量损失成本。"
    "给出客户满意度提升和问题闭环建议。"
)

ANALYSIS_AGENT_PROMPT = (
    "你是质量数据分析专家。综合来料、过程、成品、客诉多维数据，"
    "进行统计分析和趋势判断，识别关键质量问题。"
    "使用柏拉图、趋势图等方法给出数据驱动的洞见。"
)

SYNTHESIS_PROMPT = (
    "你是首席质量官。整合各专业Agent的分析结果，"
    "输出一份结构化的综合质量分析报告。\n\n"
    "报告结构：\n"
    "## 一、问题概述\n"
    "## 二、各维度分析发现\n"
    "## 三、根因推断\n"
    "## 四、风险评级\n"
    "## 五、改善建议（短期/中期/长期）\n"
    "## 六、结论\n\n"
    "要求：专业权威、数据驱动、建议可落地"
)

# =============================================================================
# 辅助函数
# =============================================================================
def get_model():
    """获取当前选择的模型（从 session state 读取，支持侧边栏切换）"""
    return st.session_state.get("selected_model", MODEL_NAME)


def call_llm(messages, temperature=0.7, max_tokens=4096, with_tools=False, model=None):
    """统一 LLM 调用封装，带错误处理和模型回退"""
    use_model = model or get_model()
    kwargs = {
        "model": use_model,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.8,
        "max_tokens": max_tokens,
    }
    if with_tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    try:
        return client.chat.completions.create(**kwargs)
    except Exception as e:
        err_msg = str(e)
        if use_model == "qwen-max":
            st.warning("⚠️ qwen-max 调用失败，自动回退到 qwen-plus")
            kwargs["model"] = "qwen-plus"
            return client.chat.completions.create(**kwargs)
        if use_model != "qwen-plus":
            st.warning(f"⚠️ {use_model} 回退到 qwen-plus")
            kwargs["model"] = "qwen-plus"
            return client.chat.completions.create(**kwargs)
        raise RuntimeError(f"API 调用失败：{err_msg[:300]}")

# =============================================================================
# UI Header
# =============================================================================
st.title("🏭 工业质量 AI Agent")
st.markdown("**全流程质量管理平台** — 覆盖来料检验 · 过程控制 · 成品检测 · 客诉处理")

# Sidebar - 全局信息
with st.sidebar:
    st.header("📋 系统信息")

    # 模型选择
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = MODEL_NAME
    current_model = st.selectbox(
        "🧠 模型选择",
        ["qwen-plus", "qwen-max"],
        index=0 if st.session_state.selected_model == "qwen-plus" else 1,
        help="qwen-max 更接近千问网页版，需在百炼控制台开通"
    )
    st.session_state.selected_model = current_model

    st.divider()
    st.metric("数据产品数", len(PRODUCTS))
    st.metric("覆盖工艺", len(PROCESSES))
    st.metric("检验记录", len(data["inspection_records"]))
    st.metric("客诉记录", len(data["complaints"]))
    st.divider()
    st.caption(f"模型：{current_model}")
    st.caption(f"数据更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("数据为仿真生成，仅供演示")

# =============================================================================
# Tabs
# =============================================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💬 智能助手",
    "🤖 多Agent协作",
    "📊 数据看板",
    "📋 报告中心",
    "📸 缺陷分析",
    "🔗 质量追溯",
    "⚖️ 供应商评分"
])

# =============================================================================
# TAB 1: 智能助手
# =============================================================================
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("质量智能问答")
    with col2:
        kb_mode = st.toggle("📚 知识库模式", help="开启后将检索质量管理知识库辅助回答")

    # 对话历史
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # 显示历史
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("问我任何质量问题… 如：A100缺陷率、冲压FMEA、SPC怎么做"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 快速判断是否需要工具：避免无关请求传 tools 影响千问原生回答
        _tool_kw = [
            r"A\d+", r"B\d+", r"C\d+", r"D\d+", r"E\d+",
            r"冲压|焊接|涂装|装配|铸造", r"LOT-", r"批次",
            r"宝钢|鞍钢|巴斯夫|PPG|博世|大陆|海拉|延锋",
            r"缺陷率|不良率|合格率|客诉|投诉",
            r"FMEA表格|生成.*表格|来料检|成品检|过程质量",
            r"供应商评分|供应商排名|追溯",
        ]
        _need_tools = kb_mode or any(re.search(kw, prompt) for kw in _tool_kw)

        if _need_tools:
            system_prompt = KNOWLEDGE_CHAT_SYSTEM if kb_mode else CHAT_SYSTEM
            response = call_llm(
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=1024, with_tools=True
            )
            assistant_message = response.choices[0].message

            if assistant_message.tool_calls:
                tool_msgs = []
                for tc in assistant_message.tool_calls:
                    func_name = tc.function.name
                    func_args = json.loads(tc.function.arguments)
                    result = available_functions[func_name](**func_args) if func_name in available_functions else f"未知工具：{func_name}"
                    tool_msgs.append({"role": "tool", "tool_call_id": tc.id, "content": result})

                follow_up = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": None, "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in assistant_message.tool_calls
                    ]},
                ] + tool_msgs
                response = call_llm(follow_up, temperature=0.7, max_tokens=4096, with_tools=False)
                assistant_message = response.choices[0].message

            answer = assistant_message.content or "抱歉，处理过程出现问题，请重试。"
        else:
            # 不需要工具：不传 system prompt，保持千问最原生输出
            response = call_llm(
                [{"role": "user", "content": prompt}],
                temperature=0.7, max_tokens=4096, with_tools=False
            )
            answer = response.choices[0].message.content

        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

    # 快捷问题
    with st.expander("💡 试试这些问题"):
        cols = st.columns(3)
        examples = [
            "A100的缺陷率最近怎么样？",
            "焊接工艺的FMEA分析",
            "SPC控制图怎么用？",
            "8D报告怎么做？",
            "查询D400的客诉情况",
            "生成冲压的FMEA表格",
        ]
        for i, ex in enumerate(examples):
            if cols[i % 3].button(ex, key=f"ex_{i}"):
                st.session_state.chat_messages.append({"role": "user", "content": ex})
                st.rerun()

# =============================================================================
# TAB 2: 多Agent协作
# =============================================================================
with tab2:
    st.subheader("🤖 多 Agent 质量分析协作")
    st.caption("Orchestrator 调度 → 多个专业 Agent 并行分析 → 首席质量官综合输出")

    # 预设场景
    col_scenario, col_custom = st.columns([2, 3])
    with col_scenario:
        scenario = st.selectbox("选择分析场景", [
            "自定义问题...",
            "A100冲压件质量下降分析",
            "B200焊接总成客诉激增",
            "C300涂装件色差问题",
            "D400装配线良率波动",
            "全厂月度质量回顾",
        ])

    if scenario == "自定义问题...":
        user_question = st.text_area("描述质量问题", placeholder="例如：A100近期缺陷率从1.2%上升到3.5%，请分析原因并给出改善建议。", height=80)
    else:
        scenario_prompts = {
            "A100冲压件质量下降分析": "产品A100（冲压件-车身侧围）近30天缺陷率从1.2%上升到3.5%，主要缺陷为裂纹和毛刺。请全面分析原因并给出改善建议。",
            "B200焊接总成客诉激增": "产品B200（焊接总成-底盘）近期收到5起客户投诉，反映气孔和未熔合问题，涉及吉利和比亚迪。请分析根因并给出8D改善方案。",
            "C300涂装件色差问题": "产品C300（涂装件-引擎盖）色差问题频发，客户退货率上升。请从全流程角度分析原因。",
            "D400装配线良率波动": "D400（装配总成-车门）产线良率波动大，Cpk从1.35降至1.02，每周约20件不良品。请分析原因。",
            "全厂月度质量回顾": "请对全厂产品进行月度质量回顾，识别TOP3质量问题和重点改善方向。",
        }
        user_question = scenario_prompts[scenario]

    if st.button("🚀 启动多Agent分析", type="primary", use_container_width=True) and user_question:
        # Phase 1: Orchestrator 规划
        with st.status("🎯 Orchestrator 正在规划分析任务...", expanded=True) as status:
            orch_response = call_llm(
                [{"role": "system", "content": ORCHESTRATOR_PROMPT}, {"role": "user", "content": user_question}],
                temperature=0.3, max_tokens=1024
            )
            try:
                orch_text = orch_response.choices[0].message.content
                orch_plan = json.loads(orch_text.replace("```json", "").replace("```", "").strip())
            except json.JSONDecodeError:
                orch_plan = {"summary": user_question, "required_agents": ["IQC", "IPQC", "OQC", "Complaint", "Analysis"]}

            st.markdown(f"**问题概述：** {orch_plan.get('summary', user_question)}")
            required = orch_plan.get("required_agents", ["IQC", "IPQC", "OQC", "Complaint", "Analysis"])
            st.info(f"📋 调用 Agent：{' → '.join(required)}")
            time.sleep(0.5)

            # Phase 2: 并行调用专业Agent
            agent_configs = {
                "IQC": {"prompt": IQC_AGENT_PROMPT, "data_func": lambda: query_incoming_inspection("A100") if "A100" in user_question else query_incoming_inspection("B200") if "B200" in user_question else query_incoming_inspection("C300") if "C300" in user_question else query_incoming_inspection("D400") if "D400" in user_question else "全产品来料数据可用"},
                "IPQC": {"prompt": IPQC_AGENT_PROMPT, "data_func": lambda: query_process_quality("冲压") if "冲压" in user_question else query_process_quality("焊接") if "焊接" in user_question else query_process_quality("涂装") if "涂装" in user_question else query_process_quality("装配")},
                "OQC": {"prompt": OQC_AGENT_PROMPT, "data_func": lambda: query_final_inspection("A100") if "A100" in user_question else query_final_inspection("B200") if "B200" in user_question else query_final_inspection("C300") if "C300" in user_question else query_final_inspection("D400") if "D400" in user_question else "多产品数据可用"},
                "Complaint": {"prompt": COMPLAINT_AGENT_PROMPT, "data_func": lambda: query_complaints("A100" if "A100" in user_question else "B200" if "B200" in user_question else None)},
                "Analysis": {"prompt": ANALYSIS_AGENT_PROMPT, "data_func": lambda: f"全厂质量数据：5产品、5工艺、{len(data['defect_details'])}条缺陷记录"},
            }

            agent_outputs = {}
            for agent_name in required:
                if agent_name in agent_configs:
                    cfg = agent_configs[agent_name]
                    st.write(f"🔍 {agent_name} Agent 分析中...")
                    agent_data = cfg["data_func"]()
                    agent_response = call_llm(
                        [
                            {"role": "system", "content": cfg["prompt"]},
                            {"role": "user", "content": f"问题：{user_question}\n\n可用数据：\n{agent_data}"}
                        ],
                        temperature=0.5, max_tokens=2048
                    )
                    agent_outputs[agent_name] = agent_response.choices[0].message.content
                    time.sleep(0.3)

            # Phase 3: Synthesis
            st.write("📝 首席质量官正在整合分析...")
            synthesis_input = f"原始问题：{user_question}\n\n"
            for name, output in agent_outputs.items():
                synthesis_input += f"### {name} Agent 分析结果：\n{output}\n\n---\n\n"

            synthesis_response = call_llm(
                [{"role": "system", "content": SYNTHESIS_PROMPT}, {"role": "user", "content": synthesis_input}],
                temperature=0.7, max_tokens=4096
            )
            final_report = synthesis_response.choices[0].message.content

            status.update(label="✅ 多 Agent 分析完成", state="complete")

        # 展示结果
        st.markdown("---")
        st.markdown("## 📊 综合质量分析报告")
        st.markdown(final_report)

        # 各Agent细节
        with st.expander("🔍 查看各 Agent 详细分析过程"):
            for name, output in agent_outputs.items():
                st.markdown(f"### {name} Agent")
                st.markdown(output)
                st.divider()

# =============================================================================
# TAB 3: 数据看板
# =============================================================================
with tab3:
    st.subheader("📊 质量数据看板")

    # 实时模式
    realtime_mode = st.toggle("🔴 实时监控模式", help="开启后每3秒自动刷新产线状态和KPI数据")

    if realtime_mode:
        st.markdown("### 🏭 产线实时状态")
        line_cols = st.columns(5)
        line_names = ["冲压线 L1", "焊接线 L2", "涂装线 L3", "装配线 L4", "铸造线 L5"]
        line_statuses = []
        for i, (col, name) in enumerate(zip(line_cols, line_names)):
            # 模拟实时状态变化（基于当前时间生成伪随机状态）
            seed_val = int(time.time() / 3) + i
            rng = random.Random(seed_val)
            status = rng.choices(
                ["running", "standby", "alarm"],
                weights=[0.75, 0.15, 0.10],
                k=1
            )[0]
            rate = round(rng.uniform(95.0, 99.9), 1)
            line_statuses.append({"name": name, "status": status, "rate": rate})
            status_icon = "🟢" if status == "running" else "🟡" if status == "standby" else "🔴"
            status_text = "运行中" if status == "running" else "待机" if status == "standby" else "⚠️ 报警"
            col.metric(
                f"{status_icon} {name}",
                f"{rate}%",
                delta=status_text,
                delta_color="normal" if status == "running" else "off" if status == "standby" else "inverse"
            )

        # 告警事件
        alarm_lines = [ls for ls in line_statuses if ls["status"] == "alarm"]
        if alarm_lines:
            for al in alarm_lines:
                st.error(f"🚨 {al['name']} 触发报警！当前良率 {al['rate']}%，请立即检查")
        else:
            st.success("✅ 所有产线运行正常，无报警事件")

        # 实时 KPI
        st.markdown("### 📡 实时数据流")
        live_cols = st.columns(4)
        live_seed = int(time.time() / 3)
        live_cols[0].metric("实时产出", f"{random.Random(live_seed).randint(800, 1200)} 件/时", delta="+12")
        live_cols[1].metric("实时不良率", f"{random.Random(live_seed+1).uniform(0.8, 2.5):.2f}%", delta=f"{random.Random(live_seed+10).uniform(-0.3, 0.3):.2f}%")
        live_cols[2].metric("在线CPK", f"{random.Random(live_seed+2).uniform(1.15, 1.5):.2f}", delta=f"{random.Random(live_seed+20).uniform(-0.08, 0.08):.2f}")
        live_cols[3].metric("设备综合效率OEE", f"{random.Random(live_seed+3).uniform(82, 95):.1f}%")

        # 最近报警历史
        with st.expander("📋 近20条告警历史"):
            alarm_history = []
            for a in range(20):
                ts = datetime.now() - timedelta(minutes=random.randint(1, 480))
                alarm_history.append({
                    "time": ts.strftime("%H:%M:%S"),
                    "line": random.choice(line_names),
                    "type": random.choice(["良率超限", "CPK偏低", "设备异常", "来料不良", "参数漂移"]),
                    "level": random.choice(["⚠️ 警告", "🔴 严重"]),
                })
            alarm_history.sort(key=lambda x: x["time"], reverse=True)
            for ah in alarm_history:
                icon = "🔴" if ah["level"] == "🔴 严重" else "🟡"
                st.markdown(f"{icon} [{ah['time']}] {ah['line']} — {ah['type']}（{ah['level']}）")

        st.divider()
        st.caption("⏱️ 数据每3秒自动刷新（模拟数据）")

    # 筛选器
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        view_products = st.multiselect("产品筛选", list(PRODUCTS.keys()), default=["A100", "B200", "C300"])
    with filter_col2:
        view_processes = st.multiselect("工艺筛选", PROCESSES, default=PROCESSES[:3])
    with filter_col3:
        view_days = st.selectbox("时间范围", [7, 30, 90, 180], index=1, format_func=lambda x: f"近{x}天")

    # 筛选数据
    filtered_records = [
        r for r in data["inspection_records"]
        if r["product_code"] in view_products
        and datetime.strptime(r["date"], "%Y-%m-%d") >= datetime.now() - timedelta(days=view_days)
    ]
    filtered_defects = [
        d for d in data["defect_details"]
        if d["product_code"] in view_products
        and d["process"] in view_processes
        and datetime.strptime(d["date"], "%Y-%m-%d") >= datetime.now() - timedelta(days=view_days)
    ]
    filtered_complaints = [
        c for c in data["complaints"]
        if c["product_code"] in view_products
        and datetime.strptime(c["date"], "%Y-%m-%d") >= datetime.now() - timedelta(days=view_days)
    ]

    # KPI 卡片
    st.markdown("### 📈 关键质量指标")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_insp = sum(r["total_inspected"] for r in filtered_records)
    total_def = sum(r["defect_count"] for r in filtered_records)
    overall_rate = round(total_def / total_insp * 100, 2) if total_insp > 0 else 0
    avg_cpk = round(sum(data["process_cpk"].get(p, 0) for p in view_processes) / len(view_processes), 2)
    complaint_closed = len([c for c in filtered_complaints if c["status"] == "已关闭"])
    complaint_total = len(filtered_complaints)

    kpi1.metric("综合良率", f"{100 - overall_rate:.1f}%", delta=f"-{overall_rate - 1.5:.2f}%")
    kpi2.metric("本月缺陷数", f"{total_def:,}", delta=f"{total_def - 200}" if total_def > 200 else f"-{200 - total_def}")
    kpi3.metric("CPK 均值", f"{avg_cpk:.2f}", delta=f"{avg_cpk - 1.33:.2f}")
    kpi4.metric("客诉关闭率", f"{complaint_closed / complaint_total * 100:.0f}%" if complaint_total > 0 else "N/A", delta=None)

    # 趋势图
    st.markdown("### 📉 缺陷率趋势")
    trend_data = {}
    for r in sorted(filtered_records, key=lambda x: x["date"]):
        date = r["date"]
        if date not in trend_data:
            trend_data[date] = {"total": 0, "defects": 0}
        trend_data[date]["total"] += r["total_inspected"]
        trend_data[date]["defects"] += r["defect_count"]

    trend_list = []
    for date, d in sorted(trend_data.items()):
        trend_list.append({
            "日期": date,
            "缺陷率(%)": round(d["defects"] / d["total"] * 100, 2) if d["total"] > 0 else 0
        })

    if trend_list:
        df_trend = pd.DataFrame(trend_list)
        st.line_chart(df_trend.set_index("日期"), use_container_width=True)

    # 帕累托图 + 缺陷分布
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### 🔴 缺陷类型帕累托")
        type_counts = Counter(d["defect_type"] for d in filtered_defects).most_common(10)
        if type_counts:
            pareto_df = pd.DataFrame(type_counts, columns=["缺陷类型", "次数"])
            pareto_df["累计占比"] = pareto_df["次数"].cumsum() / pareto_df["次数"].sum() * 100
            st.bar_chart(pareto_df.set_index("缺陷类型")["次数"], use_container_width=True)

    with col_right:
        st.markdown("### 🏭 按工艺缺陷分布")
        process_counts = Counter(d["process"] for d in filtered_defects)
        if process_counts:
            process_df = pd.DataFrame(process_counts.most_common(), columns=["工艺", "缺陷数"])
            st.bar_chart(process_df.set_index("工艺"), use_container_width=True)

    # 严重度分布
    st.markdown("### ⚠️ 缺陷严重度分布")
    sev_counts = Counter(d["severity"] for d in filtered_defects)
    sev_order = ["轻微", "中等", "严重", "致命"]
    sev_data = [{"严重度": s, "数量": sev_counts.get(s, 0)} for s in sev_order]
    sev_df = pd.DataFrame(sev_data).set_index("严重度")
    st.bar_chart(sev_df, use_container_width=True, horizontal=True)

# =============================================================================
# TAB 4: 报告中心
# =============================================================================
with tab4:
    st.subheader("📋 质量报告自动生成")

    report_col1, report_col2 = st.columns(2)
    with report_col1:
        report_type = st.selectbox("报告类型", ["日报", "周报", "月报", "8D客诉报告"])
        report_product = st.selectbox("产品范围", ["全部产品"] + list(PRODUCTS.keys()))
    with report_col2:
        report_process = st.selectbox("工艺范围", ["全部工艺"] + PROCESSES)
        report_focus = st.text_input("特殊关注点（可选）", placeholder="如：裂纹缺陷、某客户投诉等")

    report_templates = {
        "日报": "生成一份简洁的日报，包含：今日检验量、不良率、主要缺陷TOP3、异常事件、明日重点关注。",
        "周报": "生成一份周报，包含：周度质量趋势、主要质量问题、客诉情况、改善措施进展、下周计划。",
        "月报": "生成一份月度质量报告，包含：月度KPI达成情况、质量趋势分析、TOP5问题及根因、改善成果、供应商质量表现、下月重点。",
        "8D客诉报告": "按照8D方法论生成客诉分析报告：D0准备、D1团队、D2问题描述、D3临时措施、D4根因分析、D5永久措施、D6实施验证、D7防止再发。",
    }

    if st.button("📝 生成报告", type="primary", use_container_width=True):
        with st.status("正在生成报告...", expanded=True) as report_status:
            # 收集报告所需数据
            product_filter = report_product if report_product != "全部产品" else None
            process_filter = report_process if report_process != "全部工艺" else None

            # 获取相关数据
            if product_filter:
                recs = [r for r in data["inspection_records"] if r["product_code"] == product_filter]
                defects = [d for d in data["defect_details"] if d["product_code"] == product_filter]
                complaints_data = [c for c in data["complaints"] if c["product_code"] == product_filter]
            else:
                recs = data["inspection_records"]
                defects = data["defect_details"]
                complaints_data = data["complaints"]

            if process_filter:
                defects = [d for d in defects if d["process"] == process_filter]

            recent_recs = recs[-30:] if report_type == "月报" else recs[-7:] if report_type == "周报" else recs[-1:]
            total_inspected = sum(r["total_inspected"] for r in recent_recs)
            total_defects = sum(r["defect_count"] for r in recent_recs)
            avg_rate = round(total_defects / total_inspected * 100, 2) if total_inspected > 0 else 0

            type_dist = Counter(d["defect_type"] for d in defects[:200]).most_common(5)
            recent_complaints = sorted(complaints_data, key=lambda x: x["date"], reverse=True)[:5]

            # 构建数据上下文
            data_context = f"""
## 基础数据
- 统计范围：{report_type}（{recent_recs[0]['date'] if recent_recs else 'N/A'} 至 {recent_recs[-1]['date'] if recent_recs else 'N/A'}）
- 产品：{report_product}
- 工艺：{report_process}
- 总检验数：{total_inspected:,}
- 总缺陷数：{total_defects:,}
- 平均不良率：{avg_rate}%
- CPK数据：{json.dumps({p: data['process_cpk'].get(p, 0) for p in (PROCESSES if process_filter is None else [process_filter])}, ensure_ascii=False)}

## TOP5 缺陷类型
{chr(10).join(f'- {t}: {c}次' for t, c in type_dist)}

## 最近客诉
{chr(10).join(f'- [{c["date"]}] {c["customer"]}: {c["issue"]} (损失¥{c["cost"]:,})' for c in recent_complaints)}

## 特殊关注
{report_focus if report_focus else '无'}
"""

            report_prompt = f"{report_templates[report_type]}\n\n以下是数据：\n{data_context}"

            report_response = call_llm(
                [
                    {"role": "system", "content": "你是质量报告撰写专家，根据数据生成结构清晰、专业的质量报告。使用Markdown格式，包含数据和洞见。"},
                    {"role": "user", "content": report_prompt}
                ],
                temperature=0.5, max_tokens=4096
            )
            report_content = report_response.choices[0].message.content

            report_status.update(label="✅ 报告生成完成", state="complete")

        st.markdown(report_content)

        # 下载
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "📥 下载报告 (Markdown)",
                data=report_content,
                file_name=f"质量{report_type}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col_dl2:
            st.download_button(
                "📥 下载报告 (TXT)",
                data=report_content,
                file_name=f"质量{report_type}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# =============================================================================
# TAB 5: 缺陷图片分析
# =============================================================================
with tab5:
    st.subheader("📸 缺陷图片智能分析")
    st.caption("上传产品缺陷照片，AI 自动识别缺陷类型、严重度和改善建议")

    if "image_history" not in st.session_state:
        st.session_state.image_history = []

    col_upload, col_camera = st.columns(2)
    with col_upload:
        uploaded_file = st.file_uploader(
            "📁 上传缺陷照片",
            type=["jpg", "jpeg", "png", "webp"],
            help="支持 JPG/PNG/WEBP 格式"
        )
    with col_camera:
        camera_photo = st.camera_input("📷 拍照分析")

    source_image = uploaded_file or camera_photo

    # 示例按钮
    st.caption("没有照片？试试模拟分析：")
    sim_cols = st.columns(3)
    sim_scenarios = [
        ("🔧 冲压件裂纹", "冲压件表面发现一条长约3cm的裂纹，位于边缘R角处，材质为高强度钢"),
        ("🔥 焊接气孔", "焊接接头断面发现多个气孔，直径约0.5-1mm，分布在焊缝中心区域"),
        ("🎨 涂装色差", "引擎盖涂装后与车身存在明显色差，目视可见，色差仪读数ΔE=3.5"),
    ]
    for i, (label, desc) in enumerate(sim_scenarios):
        if sim_cols[i].button(label, key=f"sim_img_{i}"):
            source_image = None  # 清除上传的图片
            st.session_state["sim_description"] = desc
            st.rerun()

    # 分析图片
    if source_image:
        import base64
        image_bytes = source_image.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        col_img, col_result = st.columns([1, 2])
        with col_img:
            st.image(image_bytes, caption="上传的缺陷照片", use_container_width=True)
        with col_result:
            with st.spinner("🔍 AI 正在分析缺陷图片..."):
                user_desc = st.session_state.pop("sim_description", "")
                analysis = analyze_defect_image(image_base64, user_desc)
                st.session_state.image_history.insert(0, {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "analysis": analysis[:500],
                })

            st.markdown("### 🧠 AI 分析结果")
            st.markdown(analysis)

        # 历史记录
        if st.session_state.image_history:
            with st.expander("📋 分析历史"):
                for h in st.session_state.image_history[:10]:
                    st.caption(f"[{h['time']}]")
                    st.markdown(h["analysis"])
                    st.divider()

# =============================================================================
# TAB 6: 质量全链路追溯
# =============================================================================
with tab6:
    st.subheader("🔗 质量全链路追溯")
    st.caption("输入批次号，一键追溯从来料到客诉的全链路质量数据")

    col_trace, col_preview = st.columns([1, 2])
    with col_trace:
        batch_input = st.text_input(
            "输入批次号",
            placeholder="LOT-A100-20240601-001",
            help="格式：LOT-产品代码-日期-序号"
        )

        # 快捷选择
        st.caption("或选择示例批次：")
        sample_batches = []
        for pc in ["A100", "B200", "C300"]:
            sample_batches.extend(batch_traces[pc][:2])
        for sb in sample_batches:
            if st.button(f"📦 {sb['batch_id']}", key=f"trace_{sb['batch_id']}"):
                batch_input = sb["batch_id"]
                st.rerun()

    if batch_input:
        trace_result = trace_batch(batch_input)

        with col_preview:
            if trace_result.startswith("未找到"):
                st.warning(trace_result)
            else:
                # 解析结果并可视化展示
                lines = trace_result.split("\n")
                batch_id = lines[0].replace("批次号：", "")
                product_info = lines[1]
                date_qty = lines[2]

                st.markdown(f"### 📦 {batch_id}")
                st.markdown(f"**{product_info}** | {date_qty}")

                # 时间线展示
                st.markdown("#### ⏱️ 质量链路时间线")
                tl_cols = st.columns(5)
                steps = [
                    ("📥", "来料检验", "green"),
                    ("⚙️", "过程控制", "blue"),
                    ("📤", "成品检验", "orange"),
                    ("🚚", "出货交付", "purple"),
                    ("📋", "客诉跟踪", "red" if "⚠️ 有客诉" in trace_result else "gray"),
                ]
                for col, (icon, label, color) in zip(tl_cols, steps):
                    col.markdown(
                        f"<div style='text-align:center;padding:8px;border-radius:8px;"
                        f"background:{color}15;border:1px solid {color}40'>"
                        f"<h2>{icon}</h2><b>{label}</b></div>",
                        unsafe_allow_html=True
                    )

                # 详细数据
                st.markdown("#### 📋 详细追溯数据")
                in_section = ""
                for line in lines:
                    if line.startswith("📥"):
                        in_section = "incoming"
                        st.markdown("##### 📥 来料检验")
                    elif line.startswith("⚙️"):
                        in_section = "process"
                        st.markdown("##### ⚙️ 过程参数")
                    elif line.startswith("📤"):
                        in_section = "final"
                        st.markdown("##### 📤 成品检验")
                    elif line.startswith("🚚"):
                        in_section = "shipping"
                        st.markdown("##### 🚚 出货信息")
                    elif line.startswith("📋"):
                        in_section = "complaint"
                        st.markdown("##### 📋 客诉")
                    elif line.strip() and not line.startswith("批次号") and not line.startswith("产品"):
                        if in_section:
                            st.markdown(line)

                # 生成追溯报告按钮
                if st.button("📝 生成追溯报告", key="gen_trace_report"):
                    with st.spinner("正在生成报告..."):
                        report_response = call_llm(
                            [
                                {"role": "system", "content": "你是质量追溯专家，根据追溯数据生成专业的质量追溯报告。"},
                                {"role": "user", "content": f"请根据以下追溯数据生成一份结构化的质量追溯报告，包含：总体概述、各环节详情、风险点识别、改善建议。\n\n{trace_result}"}
                            ],
                            temperature=0.5, max_tokens=2048
                        )
                        trace_report = report_response.choices[0].message.content
                        st.markdown("---")
                        st.markdown(trace_report)
                        st.download_button(
                            "📥 下载追溯报告",
                            data=trace_report,
                            file_name=f"追溯报告_{batch_id}_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )

# =============================================================================
# TAB 7: 供应商评分看板
# =============================================================================
with tab7:
    st.subheader("⚖️ 供应商质量评分看板")
    st.caption("供应商质量绩效排名与月度趋势分析")

    # 排名
    ranked = sorted(supplier_scores.items(), key=lambda x: x[1]["overall"], reverse=True)

    st.markdown("### 🏆 综合排名")
    rank_cols = st.columns(4)
    for i, (name, s) in enumerate(ranked):
        with rank_cols[i % 4]:
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else ""
            delta_val = s["overall"] - 90
            st.metric(
                f"{medal} {name}",
                f"{s['overall']}/100",
                delta=f"{delta_val:+.1f}",
                delta_color="normal" if delta_val >= 0 else "inverse"
            )
            st.caption(f"类型：{s['info']['type']} | 产品：{'、'.join(s['info']['products'])}")
            st.progress(s["overall"] / 100)

    # 详细对比
    st.markdown("---")
    st.markdown("### 📈 各维度对比")

    # 表格数据
    comparison_data = []
    for name, s in ranked:
        latest = s["monthly"][-1]
        comparison_data.append({
            "供应商": name,
            "综合评分": s["overall"],
            "来料合格率(%)": latest["quality_rate"],
            "交货准时率(%)": latest["delivery_rate"],
            "月客诉(次)": latest["complaints"],
            "质量成本(¥)": latest["cost"],
        })
    comp_df = pd.DataFrame(comparison_data)
    st.dataframe(comp_df.set_index("供应商"), use_container_width=True)

    # 趋势图
    st.markdown("### 📉 月度评分趋势")
    selected_suppliers = st.multiselect(
        "选择供应商对比",
        list(supplier_scores.keys()),
        default=list(supplier_scores.keys())[:4]
    )
    if selected_suppliers:
        trend_rows = []
        for name in selected_suppliers:
            for m in supplier_scores[name]["monthly"]:
                trend_rows.append({
                    "供应商": name,
                    "月份": m["month"],
                    "质量合格率": m["quality_rate"],
                })
        if trend_rows:
            trend_df = pd.DataFrame(trend_rows)
            pivot = trend_df.pivot(index="月份", columns="供应商", values="质量合格率")
            st.line_chart(pivot, use_container_width=True)

    # 供应商详情
    st.markdown("---")
    st.markdown("### 🔍 供应商详情")
    detail_supplier = st.selectbox("选择供应商查看详情", list(supplier_scores.keys()))
    if detail_supplier:
        s = supplier_scores[detail_supplier]
        dt_col1, dt_col2 = st.columns(2)
        with dt_col1:
            st.markdown(f"**{detail_supplier}** — {s['info']['type']}")
            st.markdown(f"供货产品：{'、'.join(s['info']['products'])}")
            st.markdown(f"综合评分：**{s['overall']}/100**")
            st.progress(s['overall'] / 100)
        with dt_col2:
            latest = s["monthly"][-1]
            st.metric("来料合格率", f"{latest['quality_rate']}%")
            st.metric("交货准时率", f"{latest['delivery_rate']}%")
            st.metric("月客诉", f"{latest['complaints']}次")

        st.markdown("#### 月度明细")
        monthly_df = pd.DataFrame(s["monthly"])
        monthly_df = monthly_df.rename(columns={
            "month": "月份", "quality_rate": "合格率(%)",
            "delivery_rate": "准时率(%)", "complaints": "客诉(次)", "cost": "质量成本(¥)"
        })
        st.dataframe(monthly_df.set_index("月份"), use_container_width=True)

        # AI 评估
        if st.button(f"🤖 AI 评估 {detail_supplier}", key="ai_supplier"):
            with st.spinner("正在评估..."):
                supplier_report = "\n".join(
                    f"{m['month']}：质量{m['quality_rate']}% 交付{m['delivery_rate']}% 客诉{m['complaints']}次 成本¥{m['cost']:,}"
                    for m in s["monthly"]
                )
                ai_response = call_llm(
                    [
                        {"role": "system", "content": "你是供应商质量管理专家，评估供应商表现并给出改善建议。"},
                        {"role": "user", "content": f"评估供应商 {detail_supplier}（{s['info']['type']}），供货产品{'、'.join(s['info']['products'])}。\n近6个月数据：\n{supplier_report}"}
                    ],
                    temperature=0.5, max_tokens=2048
                )
                st.markdown(ai_response.choices[0].message.content)

# =============================================================================
# Footer
# =============================================================================
st.divider()
st.caption("🏭 工业质量 AI Agent | 数据为仿真生成仅供演示 | 基于通义千问 Qwen-Plus")
