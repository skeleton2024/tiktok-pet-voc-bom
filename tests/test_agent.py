"""
tests/test_agent.py
VOC Agent 单元测试
"""

import pytest
import json
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def reviews():
    """加载测试用差评数据"""
    data_file = PROJECT_ROOT / "data" / "mock_reviews.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["reviews"]


@pytest.fixture
def agent_module():
    """导入 agent 模块"""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from agent import core
    return core


@pytest.fixture
def tools_module():
    """导入 tools 模块"""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from agent import tools
    return tools


# ---------------------------------------------------------------------------
# Tests — 数据加载
# ---------------------------------------------------------------------------

class TestDataLoading:
    def test_mock_reviews_file_exists(self):
        data_file = PROJECT_ROOT / "data" / "mock_reviews.json"
        assert data_file.exists(), "mock_reviews.json 不存在"

    def test_mock_reviews_valid_json(self, reviews):
        assert isinstance(reviews, list), "reviews 应该是 list"
        assert len(reviews) > 0, "reviews 不应为空"

    def test_review_schema(self, reviews):
        required_fields = ["id", "product_name", "platform", "date", "rating", "text"]
        for review in reviews:
            for field in required_fields:
                assert field in review, f"差评缺少字段: {field}"


# ---------------------------------------------------------------------------
# Tests — 工具函数
# ---------------------------------------------------------------------------

class TestTools:
    def test_read_local_reviews(self, tools_module):
        reviews = tools_module.read_local_reviews()
        assert len(reviews) > 0, "应读取到差评数据"

    def test_identify_defect_broken_buckle(self, tools_module):
        defect = tools_module.identify_defect(
            "The buckle snapped instantly. This is dangerous."
        )
        assert defect in ["断裂", "安全隐患"], f"期望断裂/安全隐患，实际: {defect}"

    def test_identify_defect_leakage(self, tools_module):
        defect = tools_module.identify_defect(
            "The silicone hose developed cracks and water leaked onto the floor."
        )
        assert defect == "漏水", f"期望漏水，实际: {defect}"

    def test_identify_defect_safety(self, tools_module):
        defect = tools_module.identify_defect(
            "Almost lost my dog near the road. This is extremely dangerous."
        )
        assert defect == "安全隐患", f"期望安全隐患，实际: {defect}"

    def test_identify_defect_unknown(self, tools_module):
        defect = tools_module.identify_defect("It works fine.")
        assert defect in ["未识别（信息不足）", "功能丧失"], f"未识别的缺陷: {defect}"

    def test_analyze_failure_mode_brittle(self, tools_module):
        mode = tools_module.analyze_failure_mode(
            "The buckle snapped instantly with no warning.",
            defect="断裂"
        )
        assert mode == "脆性断裂", f"期望脆性断裂，实际: {mode}"

    def test_analyze_failure_mode_corrosion(self, tools_module):
        mode = tools_module.analyze_failure_mode(
            "The welding spots are rusting after 1 month.",
            defect="腐蚀"
        )
        assert mode == "腐蚀失效", f"期望腐蚀失效，实际: {mode}"

    def test_infer_root_cause_zinc_alloy_large_dog(self, tools_module):
        cause = tools_module.infer_root_cause(
            review_text="My 80lb German Shepherd pulled hard and the zinc alloy buckle broke.",
            product_name="Dog Harness",
            defect="断裂",
            failure_mode="脆性断裂",
        )
        assert "锌合金" in cause["zh"] or "brittleness" in cause["en"].lower()

    def test_infer_root_cause_silicone_leak(self, tools_module):
        cause = tools_module.infer_root_cause(
            review_text="The silicone hose cracked and leaked after 2 weeks.",
            product_name="Water Fountain",
            defect="漏水",
            failure_mode="密封失效",
        )
        assert "硅胶" in cause["zh"] or "Silicone" in cause["en"]

    def test_generate_bom_recommendation_priority_critical(self, tools_module):
        bom = tools_module.generate_bom_recommendation(
            review_id="REV-001",
            product_name="Dog Harness",
            review_text="The buckle broke and my dog almost ran into traffic. Extremely dangerous.",
            defect="安全隐患",
            failure_mode="脆性断裂",
            root_cause={"zh": "锌合金卡扣无法承受大型犬瞬时拉力", "en": "Zinc alloy cannot withstand large dog instantaneous force"},
        )
        assert bom["priority"] == "Critical"
        assert bom["status"] == "PENDING_APPROVAL"
        assert "work_order_id" in bom
        assert bom["work_order_id"].startswith("WO-")

    def test_generate_bom_recommendation_priority_high(self, tools_module):
        bom = tools_module.generate_bom_recommendation(
            review_id="REV-002",
            product_name="Water Fountain",
            review_text="The motor burned out after 3 weeks. No water flow at all.",
            defect="功能丧失",
            failure_mode="热失效",
            root_cause={"zh": "马达散热不足", "en": "Motor heat dissipation insufficient"},
        )
        assert bom["priority"] == "High"

    def test_draft_factory_email(self, tools_module):
        bom = tools_module.generate_bom_recommendation(
            review_id="REV-003",
            product_name="Dog Leash",
            review_text="The spring failed completely.",
            defect="功能丧失",
            failure_mode="机构卡滞",
            root_cause={"zh": "弹簧疲劳断裂", "en": "Spring fatigue fracture"},
        )
        email = tools_module.draft_factory_email(bom)
        assert "BOM改进工单" in email
        assert bom["work_order_id"] in email
        assert "待人工审批" in email or "PENDING" in email


# ---------------------------------------------------------------------------
# Tests — Agent 核心
# ---------------------------------------------------------------------------

class TestAgentCore:
    def test_analyze_review_returns_bom(self, agent_module):
        bom = agent_module.analyze_review(
            review_text="My 65lb golden retriever pulled and the zinc alloy buckle snapped instantly. Dangerous!",
            product_name="Dog Harness Pro",
            review_id="REV-TEST",
        )
        assert isinstance(bom, dict), "应返回 dict"
        assert "work_order_id" in bom
        assert "defect_type" in bom
        assert "priority" in bom
        assert bom["source_review_id"] == "REV-TEST"

    def test_batch_analyze_reviews(self, agent_module, reviews):
        results = agent_module.batch_analyze_reviews(reviews[:3])
        assert len(results) == 3
        for bom in results:
            assert "work_order_id" in bom
            assert "priority" in bom
            assert bom["status"] == "PENDING_APPROVAL"

    def test_bom_schema_complete(self, agent_module):
        bom = agent_module.analyze_review(
            review_text="The plastic buckle broke after one use.",
            product_name="Harness",
            review_id="REV-001",
        )
        required_keys = [
            "work_order_id", "source_review_id", "product_name",
            "defect_type", "failure_mode", "root_cause_zh", "root_cause_en",
            "material_upgrade_en", "target_cost_increase_pct", "priority",
            "reasoning_zh", "reasoning_en", "status", "created_at",
        ]
        for key in required_keys:
            assert key in bom, f"缺少字段: {key}"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
