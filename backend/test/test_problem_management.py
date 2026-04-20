"""
跨模块问题管理共享工具测试
"""
from datetime import date

import pytest

from app.core.problem_management import (
    EIGHT_D_NUMBER_PREFIX,
    ISSUE_NUMBER_PREFIX,
    PROBLEM_CATEGORY_CATALOG,
    HandlingLevel,
    ResponseMode,
    build_8d_number,
    build_issue_number,
    build_problem_category_key,
    default_response_mode,
    format_problem_number,
    get_problem_category_definition,
)


def test_problem_category_catalog_contains_confirmed_keys():
    """分类目录应覆盖当前已确认的全部编码"""

    assert set(PROBLEM_CATEGORY_CATALOG.keys()) == {
        "CQ0",
        "CQ1",
        "PQ0",
        "PQ1",
        "IQ0",
        "IQ1",
        "DQ0",
        "DQ1",
        "AQ0",
        "AQ1",
        "AQ2",
        "AQ3",
    }


def test_get_problem_category_definition_returns_expected_label():
    """分类定义应返回正确标签"""

    definition = get_problem_category_definition("AQ3")

    assert definition.category_code == "AQ"
    assert definition.subcategory_code == "3"
    assert definition.label == "客户审核问题"


def test_build_problem_category_key_from_parts():
    """分类码和子类码应能组合成标准键"""

    assert build_problem_category_key("cq", "1") == "CQ1"


def test_default_response_mode_matches_confirmed_rule():
    """处理复杂度与默认回复形式映射正确"""

    assert default_response_mode(HandlingLevel.SIMPLE) == ResponseMode.BRIEF
    assert default_response_mode(HandlingLevel.COMPLEX) == ResponseMode.BRIEF
    assert default_response_mode(HandlingLevel.MAJOR) == ResponseMode.EIGHT_D


def test_build_issue_number_uses_confirmed_format():
    """问题主单号应采用已确认格式"""

    issue_no = build_issue_number("CQ1", 3, occurred_at=date(2026, 4, 20))

    assert issue_no == "ZXQ-CQ1-2604-003"


def test_build_8d_number_uses_confirmed_format():
    """8D 报告号应采用已确认格式"""

    report_no = build_8d_number("AQ3", 1, occurred_at=date(2026, 4, 20))

    assert report_no == "ZX8D-AQ3-2604-001"


def test_format_problem_number_accepts_explicit_prefix():
    """底层格式化工具应支持显式前缀"""

    custom_no = format_problem_number(
        prefix=ISSUE_NUMBER_PREFIX,
        category_key="PQ0",
        sequence=15,
        occurred_at=date(2026, 4, 1),
    )

    assert custom_no == "ZXQ-PQ0-2604-015"


@pytest.mark.parametrize("invalid_sequence", [0, -1, 1000])
def test_format_problem_number_rejects_invalid_sequence(invalid_sequence: int):
    """流水号必须保持在三位范围内"""

    with pytest.raises(ValueError, match="Sequence"):
        format_problem_number(
            prefix=EIGHT_D_NUMBER_PREFIX,
            category_key="IQ1",
            sequence=invalid_sequence,
            occurred_at=date(2026, 4, 20),
        )


def test_build_problem_category_key_rejects_unknown_category():
    """未定义的分类组合应被拒绝"""

    with pytest.raises(ValueError, match="Unsupported problem category"):
        build_problem_category_key("ZZ", "9")
