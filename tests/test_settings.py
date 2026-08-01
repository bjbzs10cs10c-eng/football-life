"""A1：配置中心与工程骨架测试。

覆盖：15 项属性、位置加成引用校验、训练配置、综合能力权重、
配置校验函数（含失败分支）、基础常量。
"""

import pytest

import config.settings as s


def _config_snapshot():
    """复制一份当前配置 dict，供失败分支测试修改。"""
    return {k: v for k, v in vars(s).items() if k.isupper()}


# ---------- 属性系统 ----------

class TestAttributes:
    def test_total_attributes_is_15(self):
        assert len(s.ALL_ATTRIBUTES) == 15

    def test_no_duplicate_attributes(self):
        assert len(set(s.ALL_ATTRIBUTES)) == 15

    def test_group_partition(self):
        groups = [s.ATTRIBUTE_TECHNICAL, s.ATTRIBUTE_PHYSICAL, s.ATTRIBUTE_MENTAL]
        flat = [a for g in groups for a in g]
        assert flat == s.ALL_ATTRIBUTES

    def test_group_sizes(self):
        assert len(s.ATTRIBUTE_TECHNICAL) == 6
        assert len(s.ATTRIBUTE_PHYSICAL) == 5
        assert len(s.ATTRIBUTE_MENTAL) == 4

    def test_every_attribute_has_zh_name(self):
        assert set(s.ATTRIBUTE_NAMES_ZH) == set(s.ALL_ATTRIBUTES)

    def test_overall_weights_match_prd(self):
        assert s.OVERALL_WEIGHT_TECHNICAL == pytest.approx(0.40)
        assert s.OVERALL_WEIGHT_PHYSICAL == pytest.approx(0.30)
        assert s.OVERALL_WEIGHT_MENTAL == pytest.approx(0.30)
        total = (
            s.OVERALL_WEIGHT_TECHNICAL
            + s.OVERALL_WEIGHT_PHYSICAL
            + s.OVERALL_WEIGHT_MENTAL
        )
        assert total == pytest.approx(1.0)


# ---------- 位置系统 ----------

class TestPositions:
    def test_mvp_positions_exclude_gk(self):
        assert "GK" not in s.POSITION_CODES
        assert s.POSITION_CODES == ["ST", "WING", "CM", "CB"]

    def test_position_bonuses_reference_existing_attributes(self):
        for code, bonus in s.POSITION_BONUSES.items():
            assert set(bonus) <= set(s.ALL_ATTRIBUTES)

    def test_cm_bonus_maps_vision_to_decision(self):
        assert s.POSITION_BONUSES["CM"] == {"passing": 5, "decision": 5}

    def test_every_position_has_bonus_and_name(self):
        for code in s.POSITION_CODES:
            assert code in s.POSITION_BONUSES
            assert code in s.POSITION_NAMES_ZH


# ---------- 训练系统 ----------

class TestTraining:
    def test_four_training_types(self):
        assert set(s.TRAINING_TYPES) == {"TECHNICAL", "PHYSICAL", "TACTICAL", "REST"}

    def test_training_bonuses_reference_existing_attributes(self):
        for name, cfg in s.TRAINING_TYPES.items():
            assert set(cfg["attributes"]) <= set(s.ALL_ATTRIBUTES)

    def test_technical_training_affects_shooting_and_passing(self):
        assert s.TRAINING_TYPES["TECHNICAL"]["attributes"] == ["shooting", "passing"]

    def test_physical_training_affects_pace_strength_stamina(self):
        assert s.TRAINING_TYPES["PHYSICAL"]["attributes"] == ["pace", "strength", "stamina"]

    def test_tactical_training_maps_positioning_to_decision(self):
        assert s.TRAINING_TYPES["TACTICAL"]["attributes"] == ["decision"]

    def test_gain_range_is_valid(self):
        for cfg in s.TRAINING_TYPES.values():
            assert 0 <= cfg["gain_min"] <= cfg["gain_max"] <= 5

    def test_rest_restores_condition(self):
        assert s.TRAINING_TYPES["REST"]["attributes"] == []
        assert s.REST_CONDITION_RESTORE > 0


# ---------- 校验函数 ----------

class TestValidateConfig:
    def test_valid_config_passes(self):
        assert s.validate_config() is True

    def test_rejects_wrong_attribute_count(self):
        cfg = _config_snapshot()
        cfg["ALL_ATTRIBUTES"] = cfg["ALL_ATTRIBUTES"][:14]
        with pytest.raises(ValueError, match="15 项"):
            s.validate_config(cfg)

    def test_rejects_unknown_attribute_in_position_bonus(self):
        cfg = _config_snapshot()
        cfg["POSITION_BONUSES"] = dict(cfg["POSITION_BONUSES"])
        cfg["POSITION_BONUSES"]["ST"] = {"not_an_attribute": 5}
        with pytest.raises(ValueError, match="未定义属性"):
            s.validate_config(cfg)

    def test_rejects_unknown_attribute_in_training(self):
        cfg = _config_snapshot()
        cfg["TRAINING_TYPES"] = dict(cfg["TRAINING_TYPES"])
        cfg["TRAINING_TYPES"]["TECHNICAL"] = dict(cfg["TRAINING_TYPES"]["TECHNICAL"])
        cfg["TRAINING_TYPES"]["TECHNICAL"]["attributes"] = ["speed_of_light"]
        with pytest.raises(ValueError, match="未定义属性"):
            s.validate_config(cfg)

    def test_rejects_gk_position(self):
        cfg = _config_snapshot()
        cfg["POSITION_CODES"] = [*cfg["POSITION_CODES"], "GK"]
        with pytest.raises(ValueError, match="GK"):
            s.validate_config(cfg)

    def test_rejects_bad_weight_sum(self):
        cfg = _config_snapshot()
        cfg["OVERALL_WEIGHT_TECHNICAL"] = 0.5
        with pytest.raises(ValueError, match="权重"):
            s.validate_config(cfg)

    def test_rejects_unknown_tier_in_transfer_rules(self):
        cfg = _config_snapshot()
        cfg["TRANSFER_OFFER_RULES"] = dict(cfg["TRANSFER_OFFER_RULES"])
        cfg["TRANSFER_OFFER_RULES"]["MYTHIC"] = {"min_overall": 99, "min_reputation": 99}
        with pytest.raises(ValueError, match="球队等级"):
            s.validate_config(cfg)


# ---------- 基础常量 ----------

class TestBasicConstants:
    def test_start_age_is_17(self):
        assert s.START_AGE == 17

    def test_database_path_confirmed(self):
        assert s.DATABASE_PATH == "saves/football_life.db"

    def test_honors_v1_scope(self):
        assert s.HONORS_ZH == ["联赛冠军", "杯赛冠军", "金球奖"]

    def test_transfer_elite_threshold(self):
        assert s.TRANSFER_OFFER_RULES["ELITE"]["min_overall"] == 80
        assert s.TRANSFER_OFFER_RULES["ELITE"]["min_reputation"] == 70

    def test_days_per_season(self):
        assert s.DAYS_PER_SEASON == 365
