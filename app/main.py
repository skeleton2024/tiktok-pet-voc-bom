"""
app/main.py
Streamlit 主界面 — TikTok Shop Pet VOC → BOM Agent
左栏：差评输入 & Agent 推理状态
右栏：BOM 改进工单 & HITL 审批按钮
"""

import streamlit as st
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "mock_reviews.json"
SYS_PROMPT_FILE = PROJECT_ROOT / "prompts" / "system_prompt.md"

# ---------------------------------------------------------------------------
# 页面配置
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="VOC → BOM Agent",
    page_icon="🐾",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session State 初始化
# ---------------------------------------------------------------------------
if "reviews" not in st.session_state:
    st.session_state.reviews = []

if "selected_reviews" not in st.session_state:
    st.session_state.selected_reviews = []

if "bom_results" not in st.session_state:
    st.session_state.bom_results = []

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if "current_email_draft" not in st.session_state:
    st.session_state.current_email_draft = ""

if "email_edited" not in st.session_state:
    st.session_state.email_edited = ""

# ---------------------------------------------------------------------------
# 加载差评数据
# ---------------------------------------------------------------------------
@st.cache_data
def load_reviews():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("reviews", [])


def load_system_prompt():
    return SYS_PROMPT_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 供应链 Agent 推理（导入本地模块）
# ---------------------------------------------------------------------------
def run_agent_analysis(reviews):
    """运行 VOC Agent 批量分析"""
    import time
    from agent.core import analyze_review
    from agent.tools import draft_factory_email

    results = []
    total = len(reviews)

    for i, review in enumerate(reviews):
        # 模拟 Agent 思考过程（实时输出）
        with placeholder.container():
            st.spinner(f"🤖 正在分析 [{i+1}/{total}]: {review['id']} — {review['product_name']}")
            st.info(f"📖 差评文本：{review['text'][:100]}...")

        # 实际推理
        bom = analyze_review(
            review_text=review["text"],
            product_name=review["product_name"],
            review_id=review["id"],
        )

        # 生成邮件草稿
        email_draft = draft_factory_email(bom)
        bom["email_draft"] = email_draft
        results.append(bom)

        # 实时显示推理步骤（模拟 Chain of Thought 日志）
        with placeholder.container():
            col1, col2 = st.columns([1, 2])
            with col1:
                st.success(f"✅ [{i+1}/{total}] {review['id']}")
            with col2:
                st.markdown(f"""
                **Step 1 - 缺陷识别：** {bom['defect_type']}  
                **Step 2 - 失效模式：** {bom['failure_mode']}  
                **Step 3 - 根因推理：** {bom['root_cause_zh'][:50]}...  
                **Step 4 - BOM 建议：** {bom['material_upgrade_en'][:50]}...
                """)

        time.sleep(0.3)  # 短暂延迟，方便用户看清过程

    return results


# ---------------------------------------------------------------------------
# 主界面
# ---------------------------------------------------------------------------
st.title("🐾 TikTok Shop Pet VOC → BOM Agent")
st.caption("OpenClaw Hackathon 2026 · Supply Chain Engineer Agent")

# ---- 左栏 ----
with col_left := st.container():
    col_left.subheader("📋 差评分析")

    # 加载数据
    reviews = load_reviews()

    # 产品类别筛选
    product_names = list(set(r["product_name"] for r in reviews))
    selected_product = col_left.selectbox(
        "选择产品类别",
        options=["全部"] + product_names,
        index=0,
    )

    # 按产品过滤
    if selected_product == "全部":
        filtered_reviews = reviews
    else:
        filtered_reviews = [r for r in reviews if r["product_name"] == selected_product]

    col_left.markdown(f"**共 {len(filtered_reviews)} 条差评待分析**")

    # 展示差评列表
    for review in filtered_reviews:
        with col_left.expander(f"**{review['id']}** — ⭐{review['rating']} — {review['product_name']}"):
            col_left.markdown(review["text"])
            col_left.caption(f"平台：{review['platform']} | 日期：{review['date']}")

    # 分析按钮
    analyze_disabled = st.session_state.analysis_done
    if col_left.button(
        "🔍 开始 VOC 供应链分析",
        type="primary",
        disabled=analyze_disabled,
    ):
        placeholder = col_left.empty()
        st.session_state.analysis_done = True

        with st.spinner("🤖 Agent 正在执行供应链思维链推理..."):
            results = run_agent_analysis(filtered_reviews)

        st.session_state.bom_results = results
        st.session_state.selected_reviews = filtered_reviews
        st.rerun()

    # 显示已分析的 BOM 结果
    if st.session_state.bom_results:
        col_left.markdown("---")
        col_left.subheader("📊 分析结果一览")
        priority_counts = {}
        for bom in st.session_state.bom_results:
            p = bom["priority"]
            priority_counts[p] = priority_counts.get(p, 0) + 1
        for p, c in priority_counts.items():
            color = {"Critical": "🔴", "High": "🟡", "Medium": "🟢"}.get(p, "⚪")
            col_left.markdown(f"  {color} {p}: **{c}** 条")

# ---- 右栏 ----
with col_right := st.container():
    col_right.subheader("📄 BOM 改进工单")

    if not st.session_state.bom_results:
        col_right.info("⬅️ 请先在左侧点击「开始 VOC 供应链分析」")
    else:
        # 选择查看哪条工单
        wo_ids = [bom["work_order_id"] for bom in st.session_state.bom_results]
        selected_wo = col_right.selectbox("选择工单", options=wo_ids)
        selected_bom = next(b for b in st.session_state.bom_results if b["work_order_id"] == selected_wo)

        # 显示 BOM JSON
        col_right.json({k: v for k, v in selected_bom.items() if k != "email_draft"}, expanded=True)

        # 邮件草稿编辑区（HITL 断点）
        col_right.markdown("---")
        col_right.subheader("📧 BOM 改进工单 — 邮件草稿")

        email_draft = selected_bom.get("email_draft", "")

        edited_email = col_right.text_area(
            "请人工审查以下邮件内容，修改后可发送：",
            value=email_draft,
            height=350,
            key="email_edit_area",
        )

        # HITL 审批按钮
        col_right.markdown("---")
        if col_right.button("✅ 确认并发送至工厂", type="primary"):
            # 弹窗确认（不真实发送）
            st.session_state.show_success = True

        if st.session_state.get("show_success", False):
            st.success("✅ BOM 改进工单已发送至工厂！")
            st.balloons()
            st.session_state.show_success = False

        col_right.caption(
            "⚠️ 注意：此步骤仅演示 HITL 流程，不会真实发送邮件或调用外部 Webhook。"
        )

# ---------------------------------------------------------------------------
# 侧边栏：系统信息
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("ℹ️ 项目信息")
    st.markdown(f"**数据源：** 本地 `mock_reviews.json`")
    st.markdown(f"**差评总数：** {len(reviews)} 条")
    st.markdown(f"**Agent：** VOC Supply Chain Engineer v0.1")
    st.markdown(f"**框架：** OpenClaw + Streamlit")
    st.markdown("---")
    st.markdown("**约束红线：**")
    st.markdown("  🔴 禁止实时爬虫")
    st.markdown("  🔴 禁止使用数据库")
    st.markdown("  🔴 必须 HITL 人工审批")
    st.markdown("---")
    sys_prompt = load_system_prompt()
    with st.expander("📌 System Prompt"):
        st.text(sys_prompt[:500] + "..." if len(sys_prompt) > 500 else sys_prompt)
