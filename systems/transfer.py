"""俱乐部与转会系统（B9）。

TDD §11 / PRD §11：
- 转会门槛按档位配置（TRANSFER_OFFER_RULES）：综合能力 + 声望；
- 球员能达到的最高档位由低到高逐档判定；
- eligible_clubs() 返回当前可达档位及以下的全部俱乐部（排除当前球队）；
- transfer() 完成转会；工资按档位（SALARY_BY_TIER）。
年龄与比赛表现在 TDD 中未给出公式，MVP 暂不纳入，后续版本扩展。
"""

from __future__ import annotations

import config.settings as settings
import models.club as mc
from models.player import Player


def qualifies_for_tier(player: Player, tier: str) -> bool:
    """判断球员是否达到某档俱乐部的转入门槛（Overall + 声望）。"""
    if tier not in settings.TRANSFER_OFFER_RULES:
        raise ValueError(
            f"tier 非法: {tier!r}，可选 {settings.CLUB_TIERS}"
        )
    rules = settings.TRANSFER_OFFER_RULES[tier]
    return (
        player.overall() >= rules["min_overall"]
        and player.reputation >= rules["min_reputation"]
    )


def max_tier_for(player: Player) -> str | None:
    """返回球员当前能达到的最高俱乐部档位；未达任何门槛返回 None。"""
    for tier in reversed(settings.CLUB_TIERS):
        if qualifies_for_tier(player, tier):
            return tier
    return None


def eligible_clubs(
    player: Player,
    clubs: list[mc.Club] | None = None,
) -> list[mc.Club]:
    """返回球员可加入的俱乐部（档位不高于可达档位，排除当前球队）。"""
    top = max_tier_for(player)
    if top is None:
        return []
    top_index = settings.CLUB_TIERS.index(top)
    pool = clubs if clubs is not None else mc.load_clubs()
    return [
        club for club in pool
        if settings.CLUB_TIERS.index(club.tier) <= top_index
        and club.id != player.club_id
    ]


def transfer(player: Player, club: mc.Club) -> None:
    """完成转会：校验俱乐部在可加入名单内，并关联到球员。"""
    eligible_names = {c.name for c in eligible_clubs(player)}
    if club.name not in eligible_names:
        raise ValueError(
            f"俱乐部 {club.name} 不在可转会名单内（门槛不足或不在数据中）"
        )
    player.club_id = club.id
    player.validate()


def salary_for(club: mc.Club) -> int:
    """按俱乐部档位返回月薪（SALARY_BY_TIER）。"""
    return settings.SALARY_BY_TIER[club.tier]
