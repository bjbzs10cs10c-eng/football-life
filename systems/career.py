"""生涯推进系统（B10）。

PRD 核心循环“进入下一赛季” + PRD §12 经济（V1 只记录 money）+ 退役评价：
- advance_days()：按天推进日期，跨赛季 season+1 / 年龄+1，每 30 天发放工资；
- should_retire()：年龄达到 RETIRE_AGE 触发退役；
- retirement_evaluation()：按生涯统计给出退役评价。
TDD §13：一天为最小行动单位，一年 365 天。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import config.settings as settings
from models.career import Career
from models.club import Club
from models.player import Player
from systems.transfer import salary_for


@dataclass
class RetirementResult:
    """退役评价结果。"""

    label: str
    description: str


def _season_end(player: Player) -> date:
    start = date.fromisoformat(settings.SEASON_START_DATE)
    return start + timedelta(days=player.season * settings.DAYS_PER_SEASON)


def advance_days(
    player: Player,
    days: int = 1,
    club: Club | None = None,
) -> list[str]:
    """推进 N 天：跨赛季（season+1、年龄+1）、每 30 天发薪，返回过程日志。"""
    player.validate()
    if days < 1:
        raise ValueError(f"days 须为正整数，当前 {days!r}")
    if club is not None:
        club.validate()
    logs = []
    start = date.fromisoformat(settings.SEASON_START_DATE)
    current = date.fromisoformat(player.current_date)
    for _ in range(days):
        current += timedelta(days=1)
        day_index = (current - start).days
        if (
            club is not None
            and day_index > 0
            and day_index % settings.SALARY_PAY_INTERVAL_DAYS == 0
        ):
            pay = salary_for(club)
            player.money += pay
            logs.append(f"工资到账 +{pay}")
        if current >= _season_end(player):
            player.season += 1
            player.age += 1
            logs.append(
                f"赛季结束，进入第 {player.season} 赛季（年龄 {player.age}）"
            )
    player.current_date = current.isoformat()
    player.validate()
    return logs


def should_retire(player: Player) -> bool:
    """年龄达到 RETIRE_AGE 即触发退役。"""
    return player.age >= settings.RETIRE_AGE


def retirement_evaluation(
    player: Player,
    career: Career | None = None,
) -> RetirementResult:
    """按生涯统计给出退役评价（规则见 config.RETIRE_EVAL_RULES）。"""
    player.validate()
    if career is None:
        career = Career()
    career.validate()
    for rule in settings.RETIRE_EVAL_RULES:
        if (
            career.trophies >= rule["min_trophies"]
            and career.games >= rule["min_games"]
        ):
            return RetirementResult(
                label=rule["label"],
                description=rule["description"].format(trophies=career.trophies),
            )
    # 兜底：配置校验保证最后一条门槛为 0，此分支理论不可达
    return RetirementResult(label="平庸", description="足球生涯就此结束。")
