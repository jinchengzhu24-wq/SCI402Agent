import sys
from pathlib import Path

#Rubric规则文件本身有没有写完整
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci402_agent import CRITERIA_ORDER, RUBRIC_RULES, get_criterion, validate_rubric_rules


def test_all_five_criteria_exist():
    assert len(CRITERIA_ORDER) == 5
    assert set(CRITERIA_ORDER) == set(RUBRIC_RULES)


def test_each_criterion_has_required_rule_parts():
    validate_rubric_rules()

    #这个字段存在，而且不是空的
    for criterion_id in CRITERIA_ORDER:
        rule = get_criterion(criterion_id)
        assert rule["title"]
        assert rule["checklist"]
        assert rule["missing_feedback"]
        assert rule["blocking_rule"]
        assert rule["keywords"]
