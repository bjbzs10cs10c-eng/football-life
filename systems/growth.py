"""成长系统（B6）。

TDD §6：增长值 = 基础训练效果 × 职业态度系数 × 年龄系数 × 全局成长速率。
- 职业态度系数 = professionalism / MAX_ATTRIBUTE（100）；
- 年龄系数按 GROWTH_AGE_BRACKETS 分段（16-22 高速 / 23-28 正常 / 29+ 下降）；
- 结果四舍五入为整数点数，收益不足半档记为 0（年龄增长后自然下降）。
全局成长速率见 config.GROWTH_RATE，平衡调整只需改 config。
（GROWTH_ROUND_STEP 为小数累加预留，MVP 属性为整数暂不参与计算。）
"""

from __future__ import annotations

import config.settings as settings


def age_factor(age: int) -> float:
    """返回年龄对应的成长系数；超出配置区间时取最近的档位。"""
    brackets = settings.GROWTH_AGE_BRACKETS
    for low, high, factor in brackets:
        if age >= low and (high is None or age <= high):
            return factor
    if age < brackets[0][0]:
        return brackets[0][2]
    return brackets[-1][2]


def growth_amount(age: int, professionalism: int, base_gain: int) -> int:
    """按成长公式计算一次训练的整数属性增长点数。"""
    if base_gain <= 0:
        return 0
    raw = (
        base_gain
        * age_factor(age)
        * (professionalism / settings.MAX_ATTRIBUTE)
        * settings.GROWTH_RATE
    )
    return max(0, int(raw + 0.5))
