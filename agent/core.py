"""
agent/core.py
OpenClaw Agent 初始化 — VOC Supply Chain Engineer
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.md"

def get_system_prompt() -> str:
    """读取供应链工程师系统提示词"""
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# OpenClaw Agent 初始化
# ---------------------------------------------------------------------------
# 注意：OpenClaw Agent 需要完整的 SDK 环境。
# 这里使用一个兼容层，实际推理通过 tools.py 中的函数完成。
# 当 OpenClaw SDK 就绪时，可替换为：
#   from openclaw import Agent
#   AGENT = Agent(name="...", system_prompt=get_system_prompt(), tools=[...])

AGENT_NAME = "voc-supply-chain-engineer"
AGENT_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# 核心推理函数
# ---------------------------------------------------------------------------

def analyze_review(review_text: str, product_name: str, review_id: str) -> Dict[str, Any]:
    """
    主推理函数：差评文本 → BOM 改进工单（JSON）

    Chain of Thought:
    1. 缺陷识别
    2. 失效模式分析
    3. 根因推理
    4. BOM 改进建议
    """
    from agent.tools import (
        identify_defect,
        analyze_failure_mode,
        infer_root_cause,
        generate_bom_recommendation,
    )

    # Step 1: 缺陷识别
    defect = identify_defect(review_text)

    # Step 2: 失效模式
    failure_mode = analyze_failure_mode(review_text, defect)

    # Step 3: 根因推理
    root_cause = infer_root_cause(review_text, product_name, defect, failure_mode)

    # Step 4: BOM 建议
    bom = generate_bom_recommendation(
        review_id=review_id,
        product_name=product_name,
        review_text=review_text,
        defect=defect,
        failure_mode=failure_mode,
        root_cause=root_cause,
    )

    return bom


def batch_analyze_reviews(reviews: List[Dict]) -> List[Dict]:
    """批量分析差评列表，返回 BOM 工单列表"""
    results = []
    for review in reviews:
        bom = analyze_review(
            review_text=review["text"],
            product_name=review["product_name"],
            review_id=review["id"],
        )
        results.append(bom)
    return results
