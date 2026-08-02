"""成长系统（B6）。

TDD §6：增长值 = 基础训练效果 × 职业态度系数 × 年龄系数。
- 职业态度系数 = professionalism / MAX_ATTRIBUTE（100）；
- 年龄系数按 GROWTH_AGE_BRACKETS 分段（16-22 高速 / 23-28 正常 / 29+ 下降）；
- 结果先按 GROWTH_ROUND_STEP（0.5）粒度取整，再折算为整数属性点数；
- 有效训练至少 +1（MVP 属性为整数，30 岁左右的 +0.5 折算为 +1）。
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
    )
    step = settings.GROWTH_ROUND_STEP
    quantized = round(raw / step) * step
    if quantized <= 0:
        quantized = step
    return int(quantized + 0.5)
