"""
agent/tools.py

供应链工程师思维链的工具函数：
- read_local_reviews   : 读取本地 mock_reviews.json
- draft_factory_email  : 生成 BOM 工单草稿（不发送）
- identify_defect      : 缺陷识别
- analyze_failure_mode : 失效模式分析
- infer_root_cause     : 根因推理
- generate_bom_recommendation : BOM 改进建议生成
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

# ---------------------------------------------------------------------------
# 数据源工具
# ---------------------------------------------------------------------------

def read_local_reviews(filepath: str = None) -> List[Dict]:
    """
    读取本地的 mock_reviews.json 文件。
    这是唯一的数据源——禁止调用任何外部爬虫或 API。
    """
    if filepath is None:
        filepath = Path(__file__).parent.parent / "data" / "mock_reviews.json"
    else:
        filepath = Path(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("reviews", [])


def get_reviews_by_product(reviews: List[Dict], product_keyword: str) -> List[Dict]:
    """按产品名称关键词过滤差评"""
    return [
        r for r in reviews
        if product_keyword.lower() in r["product_name"].lower()
    ]


# ---------------------------------------------------------------------------
# 缺陷识别（Step 1）
# ---------------------------------------------------------------------------

DEFECT_KEYWORDS = {
    "断裂": ["snapped", "broke", "cracked", "shattered", "split", "broken", "fractured", "fails"],
    "变形": ["bent", "warped", "deformed", "flattened", "twisted", "bent out of shape"],
    "漏水": ["leaking", "leak", "water on floor", "wet floor", "dripping"],
    "功能丧失": ["stopped working", "jammed", "unresponsive", "doesn't turn", "no longer works", "broken"],
    "安全隐患": ["dangerous", "safety hazard", "almost lost", "escaped", "fire", "burning", "injury"],
    "腐蚀": ["rusted", "rusting", "corroded", "corrosion"],
    "过热": ["overheated", "burning plastic", "hot", "overheat", "burned out"],
    "磨损": ["frayed", "worn out", "tear", "torn", "scratched", "abrasion"],
}


def identify_defect(review_text: str) -> str:
    """从差评文本中识别主要缺陷类型"""
    text_lower = review_text.lower()
    detected = []

    for defect_type, keywords in DEFECT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                detected.append(defect_type)
                break

    if not detected:
        return "未识别（信息不足）"
    # 返回最严重的缺陷（按优先级）
    priority = ["安全隐患", "断裂", "功能丧失", "过热", "漏水", "腐蚀", "变形", "磨损"]
    for p in priority:
        if p in detected:
            return p
    return detected[0]


# ---------------------------------------------------------------------------
# 失效模式分析（Step 2）
# ---------------------------------------------------------------------------

FAILURE_MODE_PATTERNS = [
    ("脆性断裂", ["snapped", "brittle", "instant", "immediately", "no warning"]),
    ("疲劳断裂", ["after weeks", "after months", "gradual", "slowly", "progressive"]),
    ("塑性变形", ["bent", "deformed", "warped", "stretched", "permanently"]),
    ("腐蚀失效", ["rusted", "corroded", "rust", "corrosion", "oxidation"]),
    ("磨损失效", ["frayed", "worn", "tear", "torn", "rubbed raw", "abrasion"]),
    ("热失效", ["overheated", "burned out", "burning", "hot", "heat"]),
    ("机构卡滞", ["jammed", "stuck", "won't lock", "stiff", "clicking"]),
]


def analyze_failure_mode(review_text: str, defect: str) -> str:
    """根据缺陷类型和文本模式分析失效模式"""
    text_lower = review_text.lower()

    for mode, patterns in FAILURE_MODE_PATTERNS:
        if any(p in text_lower for p in patterns):
            return mode

    # 默认映射
    default_map = {
        "断裂": "脆性断裂",
        "变形": "塑性变形",
        "漏水": "密封失效",
        "功能丧失": "机构卡滞",
        "安全隐患": "脆性断裂",
        "腐蚀": "腐蚀失效",
        "过热": "热失效",
        "磨损": "磨损失效",
    }
    return default_map.get(defect, "未知失效模式")


# ---------------------------------------------------------------------------
# 根因推理（Step 3）
# ---------------------------------------------------------------------------

ROOT_CAUSE_RULES: List[Tuple[str, str, str, str]] = [
    # (触发词/模式, 缺陷类型, 根因_zh, 根因_en)
    (
        "zinc alloy|锌合金|zinc",
        "断裂",
        "锌合金脆性高（延伸率<1%），无法吸收冲击能量，瞬时应力超过断裂强度",
        "Zinc alloy has high brittleness (elongation <1%) and cannot absorb impact energy; instantaneous stress exceeds fracture strength"
    ),
    (
        "large breed|big dog|golden retriever|labrador|german shepherd|65lb|70lb|80lb|大型",
        "断裂",
        "大型犬瞬时拉力可达200-350N，普通金属材料无法承受",
        "Large breed instantaneous pulling force reaches 200-350N, exceeding the capacity of standard metal materials"
    ),
    (
        "plastic buckle|plastic strap|聚甲醛|POM|polyoxymethylene",
        "断裂",
        "POM在低温或持续循环应力下发生蠕变断裂",
        "POM experiences creep fracture under low temperature or sustained cyclic stress"
    ),
    (
        "silicone|硅胶|硅橡胶",
        "漏水",
        "硅胶长期耐热水循环导致交联链断裂，出现微裂纹漏水",
        "Silicone cross-linking chains fracture under prolonged hot water循环, causing micro-crack leakage"
    ),
    (
        "spring|弹簧|recoil",
        "功能丧失",
        "弹簧材料（65Mn）疲劳极限不足，循环使用后弹性衰减",
        "Spring material (65Mn) has insufficient fatigue limit, causing elastic degradation after cyclic use"
    ),
    (
        "weld|焊接|焊缝",
        "腐蚀",
        "焊接热影响区（HAZ）奥氏体结构被破坏，铬含量降至12%以下，失去耐腐蚀性",
        "Weld HAZ destroys austenitic structure, reducing chromium content below 12%, losing corrosion resistance"
    ),
    (
        "motor|马达|motor burned|motor overheating",
        "过热",
        "马达散热设计不足，线圈温度超过F级绝缘上限（155°C）",
        "Insufficient motor heat dissipation design; coil temperature exceeds F-class insulation limit (155°C)"
    ),
    (
        "zipper|拉链|seam|接缝",
        "断裂",
        "拉链头材质为普通锌合金，抗剪切强度不足，接缝工艺不良",
        "Zipper head made of ordinary zinc alloy with insufficient shear strength; poor seam craftsmanship"
    ),
    (
        "adapter|适配器|power adapter",
        "过热",
        "电源适配器输出功率余量不足（<20%），持续满载运行导致温升超标",
        "Power adapter output power margin insufficient (<20%); continuous full-load operation causes temperature rise to exceed standard"
    ),
    (
        "reflective|反光|stitching|缝线",
        "断裂",
        "反光条采用普通涤纶线，耐磨性不足，水洗后脱落",
        "Reflective strip uses ordinary polyester thread with insufficient abrasion resistance; detaches after washing"
    ),
    (
        "padding|padding flattened|肩垫|护垫压扁",
        "变形",
        "EVA发泡垫密度不足（<25kg/m³），压缩永久变形率超标",
        "EVA foam pad density insufficient (<25kg/m³); compression set exceeds standard"
    ),
    (
        "feeder|auger|螺旋|自动喂食器",
        "功能丧失",
        "螺旋推进器与电机轴连接采用摩擦配合，长时间运行后松动打滑",
        "Auger and motor shaft connection uses friction fit; loosens and slips after prolonged operation"
    ),
    (
        "uv|uv lamp|uv sterilization|紫外线|杀菌灯",
        "功能丧失",
        "UVC灯珠（265nm）寿命设计不足（<5000h），驱动电路无恒流保护",
        "UVC LED (265nm) lifetime design insufficient (<5000h); driver circuit lacks constant current protection"
    ),
    (
        "carrier|笼|transport|pet carrier",
        "断裂",
        "折叠宠物箱连接轴采用普通钢材，剪切强度不足",
        "Foldable pet carrier hinge shaft uses ordinary steel with insufficient shear strength"
    ),
    (
        "stand|支架|elevation|elevated bowl",
        "断裂",
        "elevation platform采用普通PP塑料，弯曲强度不足大型犬体重负荷",
        "Elevation platform uses ordinary PP plastic with insufficient flexural strength for large breed weight load"
    ),
]


def infer_root_cause(
    review_text: str,
    product_name: str,
    defect: str,
    failure_mode: str,
) -> Dict[str, str]:
    """推理根因，返回中英双语根因描述"""
    text_lower = review_text.lower()
    combined = f"{product_name} {text_lower}"

    for pattern, _, cause_zh, cause_en in ROOT_CAUSE_RULES:
        if re.search(pattern, combined, re.IGNORECASE):
            return {"zh": cause_zh, "en": cause_en}

    # 默认根因（无法精确匹配时）
    default_cause_zh = (
        f"当前{product_name}使用的材料/工艺无法承受实际使用场景下的应力，"
        f"属于典型的{failure_mode}，建议进行材料升级或结构加固"
    )
    default_cause_en = (
        f"The current material/process used in {product_name} cannot withstand the stress "
        f"of actual use scenario. This is a typical case of {failure_mode}. "
        f"Material upgrade or structural reinforcement is recommended."
    )
    return {"zh": default_cause_zh, "en": default_cause_en}


# ---------------------------------------------------------------------------
# BOM 改进建议（Step 4）
# ---------------------------------------------------------------------------

MATERIAL_UPGRADE_MAP = {
    "锌合金卡扣": ("AZ91D镁合金 → 7075-T6航空铝合金", "Zinc die-cast → 7075-T6 Aerospace Aluminum Alloy"),
    "POM塑料": ("POM → 玻璃纤维增强PA66（GF30%）", "POM → Glass Fiber Reinforced PA66 (GF30%)"),
    "普通PP": ("PP → 矿物填充PP（MD20%）或ABS", "Ordinary PP → Mineral Filled PP (MD20%) or ABS"),
    "65Mn弹簧钢": ("65Mn → 琴钢线SWP-B或不锈钢304", "65Mn → Piano Wire SWP-B or SS304"),
    "普通不锈钢": ("SS201 → SS316L（钼含量2-3%）", "SS201 → SS316L (Mo content 2-3%)"),
    "涤纶缝线": ("普通涤纶 → 高强涤纶（1000D以上）", "Ordinary Polyester → High-Strength Polyester (1000D+)"),
    "EVA发泡": ("EVA25kg/m³ → EVA45kg/m³或PU发泡", "EVA25kg/m³ → EVA45kg/m³ or PU Foam"),
    "普通螺旋": ("PA66+GF30 → PEEK（耐高温耐磨）", "PA66+GF30 → PEEK (High Temp & Wear Resistant)"),
    "锌合金拉链头": ("Zinc die-cast → Zinc alloy + electrophoresis coating",),
}


def generate_bom_recommendation(
    review_id: str,
    product_name: str,
    review_text: str,
    defect: str,
    failure_mode: str,
    root_cause: Dict[str, str],
) -> Dict[str, Any]:
    """生成完整的 BOM 改进工单"""
    # 生成工单ID
    year = datetime.now().year
    seq = int(review_id.replace("REV-", "").replace("REV", ""))
    wo_id = f"WO-{year}-{seq:03d}"

    # 判断优先级
    safety_keywords = ["dangerous", "safety", "almost lost", "escaped", "fire", "injury"]
    text_lower = review_text.lower()
    if any(kw in text_lower for kw in safety_keywords) or defect == "安全隐患":
        priority = "Critical"
    elif defect in ["断裂", "功能丧失", "过热"]:
        priority = "High"
    else:
        priority = "Medium"

    # 推理材料升级建议
    current_spec_en = "Zinc alloy / POM / Ordinary steel / PP plastic (see actual product)"
    recommended_spec_en = "Material upgrade required — see root cause analysis"

    # 尝试匹配具体升级建议
    material_upgrade_en = "Aviation-grade aluminum alloy or forged stainless steel (case-by-case basis)"
    cost_increase_pct = 15  # 默认15%

    for pattern, upgrades in MATERIAL_UPGRADE_MAP.items():
        if pattern.lower() in f"{product_name} {review_text}".lower():
            if isinstance(upgrades, tuple):
                material_upgrade_en = upgrades[1]
            if priority == "Critical":
                cost_increase_pct = 20
            elif priority == "High":
                cost_increase_pct = 15
            else:
                cost_increase_pct = 10
            break

    bom = {
        "work_order_id": wo_id,
        "source_review_id": review_id,
        "product_name": product_name,
        "defect_type": defect,
        "failure_mode": failure_mode,
        "root_cause_zh": root_cause["zh"],
        "root_cause_en": root_cause["en"],
        "current_spec_zh": "需根据实际BOM确认（建议补充材料规格表）",
        "current_spec_en": current_spec_en,
        "recommended_spec_zh": "见 root_cause，建议进行材料升级验证",
        "recommended_spec_en": recommended_spec_en,
        "material_upgrade_en": material_upgrade_en,
        "target_cost_increase_pct": cost_increase_pct,
        "priority": priority,
        "reasoning_zh": (
            f"根据差评描述：'{review_text[:80]}...' "
            f"判定为{defect}（{failure_mode}），{root_cause['zh']}"
        ),
        "reasoning_en": (
            f"Based on review: '{review_text[:80]}...' "
            f"Identified as {defect} ({failure_mode}). {root_cause['en']}"
        ),
        "status": "PENDING_APPROVAL",
        "created_at": datetime.now().isoformat(),
    }

    return bom


# ---------------------------------------------------------------------------
# 邮件草稿工具（虚构，不发送）
# ---------------------------------------------------------------------------

def draft_factory_email(bom: Dict[str, Any]) -> str:
    """
    生成发给 1688 代工厂的 BOM 改进工单邮件草稿。
    注意：此函数仅生成文本，不实际发送任何邮件。
    所有外部通信必须经过 HITL 人工审批。
    """
    email_body = f"""
Subject: 【BOM改进工单】{bom['product_name']} — {bom['work_order_id']}

尊敬的 {bom['product_name']} 代工厂负责人：

您好。我们是 TikTok Shop 宠物用品品牌方，现发来以下 BOM 改进工单，请贵司工程团队评估并回复。

{'='*60}
工单编号：{bom['work_order_id']}
优先级：{bom['priority']}
产品名称：{bom['product_name']}
关联差评ID：{bom['source_review_id']}
{'='*60}

一、缺陷类型（Defect Type）
{bom['defect_type']}

二、失效模式（Failure Mode）
{bom['failure_mode']}

三、根因分析（Root Cause Analysis）
{bom['root_cause_zh']}

Root Cause (EN):
{bom['root_cause_en']}

四、当前规格 vs 建议规格
当前规格：{bom['current_spec_zh']}
建议规格：{bom['recommended_spec_zh']}

Current Spec: {bom['current_spec_en']}
Recommended Spec: {bom['recommended_spec_en']}

五、材料升级建议
{bom['material_upgrade_en']}

六、目标成本增幅
{bom['target_cost_increase_pct']}%（请在回复中确认具体价格）

七、推理依据
{bom['reasoning_zh']}

---
此工单由 VOC Supply Chain Agent 自动生成，
须经品牌方人工审批后方可正式发送。
    """
    return email_body.strip()
