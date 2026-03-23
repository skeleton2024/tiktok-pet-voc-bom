# PRD — TikTok Shop Pet Products VOC → BOM Agent

> OpenClaw Hackathon 2026 · Project `tiktok-pet-voc-bom`

---

## 1. Concept & Vision

**What it does:**  
读取 TikTok Shop 宠物用品（饮水机、牵引绳等）的非结构化差评，通过具备"供应链工程师"思维 的 Agent 输出结构化 BOM 改进工单。

**What it does NOT do:**  
- 不爬取任何外部网站（数据源：本地 `./data/mock_reviews.json`）
- 不连接任何数据库（状态全在 `st.session_state`）
- 不自动外发任何邮件或 Webhook（HITL 人工审批是硬性断点）

**Core differentiator:**  
主流 VOC 工具做"文本归纳"，我们做"因果推理"。Agent 不是翻译差评，而是扮演供应链工程师——识别物理失效模式，推断材料/工艺根因，给出具体的 BOM 修改建议。

---

## 2. Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit UI (app.py)                                       │
│  ┌──────────────────────┐  ┌─────────────────────────────┐  │
│  │  Left: 差评输入&状态  │  │  Right: Agent 推理 & 工单    │  │
│  │  - 读取本地 JSON     │  │  - Spinner 思考动画          │  │
│  │  - 实时显示进度       │  │  - BOM 改进工单渲染          │  │
│  └──────────────────────┘  │  - HITL 审批按钮             │  │
│                             └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │ Tool Call
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  OpenClaw Agent (agent.py)                                   │
│  - system_prompt: 供应链工程师人设                            │
│  - Tools: read_local_reviews, draft_factory_email            │
│  - Chain of Thought: 差评 → 缺陷分类 → 根因分析 → BOM建议    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  mock_reviews.json (./data/)                                │
│  - 50条预设极端差评（宠物饮水机/牵引绳）                      │
│  - 字段: id, product_name, platform, date, rating, text     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Data Schema — mock_reviews.json

```json
{
  "reviews": [
    {
      "id": "REV-001",
      "product_name": "Pet Water Fountain DR-V3",
      "platform": "TikTok Shop",
      "date": "2026-02-14",
      "rating": 1,
      "text": "My golden retriever (65lbs) pulled hard during walk and the buckle snapped instantly. Almost lost him near the road. This is dangerously weak."
    }
  ]
}
```

---

## 4. Agent System Prompt — 供应链工程师人设

核心指令（中文 + 英文双语思维链）：

```
你是一名拥有 10 年经验的宠物用品供应链工程师。
你的任务是分析 TikTok Shop 差评，并输出专业 BOM 改进工单。

你的思维链（Chain of Thought）必须严格遵循以下步骤：

Step 1 — 缺陷识别（Defect Identification）
  从差评中提取物理失效现象：断裂/变形/漏水/功能丧失/安全隐患

Step 2 — 失效模式分析（Failure Mode Analysis）
  判断失效类型：
  - 脆性断裂（Brittle Fracture）→ 材料韧性不足
  - 疲劳断裂（Fatigue Fracture）→ 循环应力超限
  - 塑性变形（Plastic Deformation）→ 屈服强度不足
  - 腐蚀失效（Corrosion Failure）→ 材料耐腐蚀性差

Step 3 — 根因推理（Root Cause Inference）
  基于失效模式，推断材料/工艺/设计问题：
  - "锌合金卡扣" + "大型犬瞬时拉力" → 脆性断裂风险
  - "普通塑料" + "冬季低温" → 低温脆化

Step 4 — BOM 改进建议（BOM Improvement Recommendation）
  输出具体修改：
  - 材料升级建议（牌号/规格/强度参数）
  - 目标成本增幅（%）
  - 优先级：Critical / High / Medium

输出格式：结构化 JSON（见下方 BOM 工单 Schema）
```

---

## 5. BOM Improvement Work Order — Schema

```json
{
  "work_order_id": "WO-2026-001",
  "source_review_id": "REV-001",
  "product_name": "Pet Water Fountain DR-V3",
  "defect_type": "物理断裂",
  "failure_mode": "脆性断裂",
  "root_cause": "锌合金卡扣屈服强度不足，无法承受大型犬瞬时拉力",
  "current_spec": "锌合金压铸卡扣，壁厚2mm",
  "recommended_spec": "航空铝合金（7075-T6）或锻造不锈钢（SS316）卡扣，壁厚≥3mm",
  "material_upgrade": "AZ91D 镁合金 → 7075-T6 航空铝合金",
  "target_cost_increase_pct": 18,
  "priority": "Critical",
  "reasoning_zh": "大型犬瞬时拉力可达200N以上，普通锌合金脆性断裂风险极高",
  "reasoning_en": "Large breed instantaneous pulling force exceeds 200N, making conventional zinc alloy highly susceptible to brittle fracture"
}
```

---

## 6. UI Layout — Streamlit

### 页面标题
`🐾 TikTok Shop Pet VOC → BOM Agent`

### 左栏（60% 宽度）
| 组件 | 说明 |
|------|------|
| `st.title` | 页面标题 |
| `st.selectbox` | 选择产品类别（Water Fountain / Harness / Feeder） |
| `st.button("🔍 分析差评")` | 触发 Agent |
| `st.spinner` | 思考中动画 + Agent 思考日志实时输出 |
| `st.json` | 展示中间推理结果（JSON 折叠面板） |

### 右栏（40% 宽度）
| 组件 | 说明 |
|------|------|
| `st.subheader("📋 BOM 改进工单")` | 工单标题 |
| `st.text_area`（readonly=False, 初始为 readonly） | 可编辑工单文本，供人工确认 |
| `st.button("✅ 确认并发送至工厂")` | HITL 断点，点击后弹 `st.success("工单已发送！")` |
| `st.caption` | 提示：此步骤不会真实发送邮件 |

### 加载状态
Agent 思考时，左栏显示：
```
🤖 供应链 Agent 正在分析...
✅ Step 1: 缺陷识别完成
✅ Step 2: 失效模式分析完成
✅ Step 3: 根因推理完成
✅ Step 4: BOM 建议生成完成
```

---

## 7. File Structure

```
tiktok-pet-voc-bom/
├── README.md
├── requirements.txt
├── PRD.md
├── .gitignore
│
├── data/
│   └── mock_reviews.json          # 50条预设差评
│
├── agent/
│   ├── __init__.py
│   ├── core.py                    # OpenClaw Agent 初始化 + system_prompt
│   └── tools.py                   # Tool 函数（read_local_reviews, draft_factory_email）
│
├── app/
│   ├── __init__.py
│   └── main.py                    # Streamlit 主页面
│
├── prompts/
│   └── system_prompt.md           # 供应链工程师系统提示词
│
└── tests/
    └── test_agent.py              # 单元测试（读取JSON / Agent推理 / BOM Schema校验）
```

---

## 8. Hard Constraints Checklist

| # | 约束 | 状态 |
|---|------|------|
| H1 | 禁止实时爬虫，数据源仅限本地 `mock_reviews.json` | 🔴 实施中 |
| H2 | 禁止使用任何数据库（MySQL/PostgreSQL/SQLite） | 🔴 实施中 |
| H3 | Agent 不能自动发送邮件，必须有 HITL 审批断点 | 🔴 实施中 |
| H4 | 所有状态流转在 `st.session_state` 内完成 | 🔴 实施中 |

---

## 9. OpenClaw Integration Spec

OpenClaw 将作为 Agent 推理引擎：

```python
# agent/core.py 核心逻辑
from openclaw import Agent

AGENT = Agent(
    name="voc-supply-chain-engineer",
    system_prompt=open("prompts/system_prompt.md").read(),
    tools=["read_local_reviews", "draft_factory_email"],
)

def analyze_review(review_text: str) -> dict:
    """主推理函数：差评文本 → BOM 工单"""
    result = AGENT.run(f"分析以下差评，输出BOM改进工单：{review_text}")
    return result
```

---

## 10. Success Metrics

- [ ] 成功读取 `mock_reviews.json` 并解析
- [ ] Agent 对 50 条差评完成根因推理（至少 10 条 Critical 级别）
- [ ] BOM 工单 JSON Schema 校验 100% 通过
- [ ] Streamlit UI 完整展示左右分栏布局
- [ ] HITL 审批按钮触发 `st.success` 弹窗
- [ ] GitHub 仓库包含完整代码 + PRD + README

---

## 11. Timeline

| Phase | 内容 | 状态 |
|-------|------|------|
| P1 | PRD + 项目骨架 + mock_reviews.json 生成 | ⬜ 进行中 |
| P2 | Agent 核心代码（OpenClaw 集成 + Tools） | ⬜ 待开始 |
| P3 | Streamlit UI + HITL 逻辑 | ⬜ 待开始 |
| P4 | 测试 + README + 最终推送 | ⬜ 待开始 |

---

*Document Version: v0.1 · 2026-03-23 · Claw 🐾*
