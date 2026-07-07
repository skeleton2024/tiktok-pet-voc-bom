# TikTok Shop Pet VOC to BOM Agent

OpenClaw Hackathon 2026 supply-chain agent prototype.

This project turns mock TikTok Shop pet-product complaints into structured BOM improvement work orders. It is positioned as a hackathon-style agent workflow prototype, not a production crawler, production supply-chain system, or trained ML model.

## Problem

Pet-product reviews often contain vague complaints such as broken leashes, leaking fountains, or unsafe materials. A supply-chain engineer needs to translate those complaints into concrete failure modes and BOM improvement actions.

This prototype explores that workflow:

```text
review
-> defect identification
-> failure-mode analysis
-> root-cause hypothesis
-> BOM recommendation
-> human approval
```

## Core Capabilities

- Reads local mock reviews from `./data/mock_reviews.json`.
- Identifies defect types such as fracture, leakage, functional failure, and safety issues.
- Maps complaints to possible failure modes and root-cause hypotheses.
- Generates structured BOM improvement work orders.
- Keeps a human-in-the-loop approval step before any external action.

## Example

```text
Review: "The dog leash snapped during a walk."

Output:
- defect type: fracture
- possible failure mode: brittle fracture / overload
- root-cause hypothesis: insufficient buckle material strength for high impulse force
- BOM recommendation: upgrade buckle material and mark cost impact
- status: pending human approval
```

## Tech Stack

| Layer | Tech |
|---|---|
| Agent workflow | OpenClaw-style tool calls and structured reasoning steps |
| UI | Streamlit |
| Data | Local mock reviews, no crawler |
| State | `st.session_state`, no database |
| Approval | Human-in-the-loop checkpoint |

## Repository Structure

```text
tiktok-pet-voc-bom/
├── README.md
├── requirements.txt
├── PRD.md
├── .gitignore
├── data/
│   └── mock_reviews.json
├── agent/
│   ├── __init__.py
│   ├── core.py
│   └── tools.py
├── app/
│   ├── __init__.py
│   └── main.py
├── prompts/
│   └── system_prompt.md
└── tests/
    └── test_agent.py
```

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app/main.py
PYTHONPATH=. pytest tests/test_agent.py -v
```

## Hard Constraints

| Constraint | Description |
|---|---|
| No realtime crawling | Data source is limited to local mock reviews |
| No production database | State is kept in `st.session_state` |
| Human approval required | The agent does not automatically send external messages or execute procurement actions |

## Sample Output

```json
{
  "work_order_id": "WO-2026-001",
  "source_review_id": "REV-001",
  "product_name": "Dog Harness Pro",
  "defect_type": "fracture",
  "failure_mode": "brittle fracture",
  "root_cause": "Zinc alloy buckle may be too brittle for high impulse force",
  "material_upgrade": "Zinc die-cast -> 7075-T6 aluminum alloy",
  "target_cost_increase_pct": 18,
  "priority": "Critical",
  "status": "PENDING_APPROVAL"
}
```

## What This Project Proves

- Fast domain abstraction in a hackathon setting.
- Agent workflow design around tools, structured outputs, and HITL approval.
- Ability to turn unstructured product feedback into an engineering action format.

## Limitations

- Uses local mock data only.
- The current logic is prototype-oriented and partly rule-based.
- It is not a production supply-chain optimization engine.
- It is not a trained ML model.
