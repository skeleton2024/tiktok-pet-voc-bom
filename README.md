# 🐾 TikTok Shop Pet VOC → BOM Agent

> OpenClaw Hackathon 2026 · Supply Chain Engineer Agent

读取 TikTok Shop 宠物用品（饮水机、牵引绳）的非结构化差评，通过**供应链工程师思维链**推理，输出结构化 BOM 改进工单。

---

## 核心能力

不是"翻译差评"，而是**"因果推理"**：

```
❌ 差评："狗绳断了"
↓  普通 VOC 工具
✅ 翻译："产品质量差"

↓  本项目 Agent
✅ 推理："大型犬瞬时拉力 > 200N，普通锌合金卡扣发生脆性断裂"
✅ 输出："建议升级为 7075-T6 航空铝合金卡扣（成本 +18%）"
```

---

## 技术架构

| 层级 | 技术 |
|------|------|
| Agent 引擎 | OpenClaw（Tool 调用 + Chain of Thought） |
| UI 框架 | Streamlit（左右分栏） |
| 数据源 | 本地 `./data/mock_reviews.json`（禁止爬虫） |
| 状态管理 | `st.session_state`（零数据库） |
| 审批机制 | HITL 人工断点（不自动外发） |

---

## 目录结构

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
│   ├── core.py                    # Agent 初始化 + analyze_review()
│   └── tools.py                   # 供应链工具函数
│
├── app/
│   ├── __init__.py
│   └── main.py                    # Streamlit 主界面
│
├── prompts/
│   └── system_prompt.md           # 供应链工程师系统提示词
│
└── tests/
    └── test_agent.py              # 单元测试
```

---

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行 Streamlit UI
streamlit run app/main.py

# 3. 运行测试
PYTHONPATH=. pytest tests/test_agent.py -v
```

---

## 约束红线（Hard Constraints）

| # | 约束 | 说明 |
|---|------|------|
| H1 | 禁止实时爬虫 | 数据源仅限本地 `mock_reviews.json` |
| H2 | 禁止数据库 | 所有状态在 `st.session_state` |
| H3 | HITL 审批 | Agent 不能自动发送邮件，必须人工确认 |

---

## 思维链（Chain of Thought）

```
Step 1: 缺陷识别        → 断裂 / 漏水 / 功能丧失 / 安全隐患...
Step 2: 失效模式分析    → 脆性断裂 / 疲劳断裂 / 腐蚀失效 / 热失效...
Step 3: 根因推理        → 材料问题 / 工艺问题 / 设计余量不足...
Step 4: BOM 改进建议    → 材料升级 + 成本增幅 + 优先级
```

---

## 输出示例

```json
{
  "work_order_id": "WO-2026-001",
  "source_review_id": "REV-001",
  "product_name": "Dog Harness Pro",
  "defect_type": "断裂",
  "failure_mode": "脆性断裂",
  "root_cause_zh": "锌合金脆性高，无法吸收大型犬瞬时冲击能量",
  "material_upgrade_en": "Zinc die-cast → 7075-T6 Aerospace Aluminum Alloy",
  "target_cost_increase_pct": 18,
  "priority": "Critical",
  "status": "PENDING_APPROVAL"
}
```

---

## GitHub

https://github.com/skeleton2024/tiktok-pet-voc-bom
