from __future__ import annotations

from ehrlich.nutrition.domain.dri import DRIValues, get_dri, list_nutrients


class TestGetDri:
    def test_vitamin_c_adult_male(self) -> None:
        v = get_dri("vitamin_c", "adult", "male")
        assert v is not None
        assert v.ear == 75
        assert v.rda == 90
        assert v.ul == 2000
        assert v.unit == "mg"

    def test_iron_adult_female(self) -> None:
        v = get_dri("iron", "adult", "female")
        assert v is not None
        assert v.rda == 18
        assert v.ear == 8.1

    def test_iron_adult_male(self) -> None:
        v = get_dri("iron", "adult", "male")
        assert v is not None
        assert v.rda == 8

    def test_iron_sex_difference(self) -> None:
        male = get_dri("iron", "adult", "male")
        female = get_dri("iron", "adult", "female")
        assert male is not None and female is not None
        assert female.rda > male.rda  # 18 vs 8

    def test_calcium_teen_vs_adult(self) -> None:
        teen = get_dri("calcium", "teen", "male")
        adult = get_dri("calcium", "adult", "male")
        assert teen is not None and adult is not None
        assert teen.rda == 1300
        assert adult.rda == 1000

    def test_vitamin_d_elderly(self) -> None:
        v = get_dri("vitamin_d", "elderly", "male")
        assert v is not None
        assert v.rda == 20  # higher than adult 15

    def test_folate_pregnant(self) -> None:
        v = get_dri("folate", "pregnant", "female")
        assert v is not None
        assert v.rda == 600
        assert v.ear == 520

    def test_vitamin_k_ai_only(self) -> None:
        v = get_dri("vitamin_k", "adult", "male")
        assert v is not None
        assert v.ear is None
        assert v.rda is None
        assert v.ai == 120
        assert v.ul is None

    def test_unknown_nutrient_returns_none(self) -> None:
        assert get_dri("unobtainium") is None

    def test_unknown_age_group_falls_back_to_adult(self) -> None:
        v = get_dri("vitamin_c", "unknown_group", "male")
        assert v is not None
        assert v.rda == 90  # adult male fallback

    def test_space_and_case_normalization(self) -> None:
        v = get_dri("Vitamin C")
        assert v is not None
        assert v.rda == 90

    def test_dri_values_frozen(self) -> None:
        v = get_dri("calcium")
        assert v is not None
        try:
            v.rda = 9999  # type: ignore[misc]
            raise AssertionError("Should have raised FrozenInstanceError")
        except AttributeError:
            pass


class TestListNutrients:
    def test_returns_at_least_28(self) -> None:
        nutrients = list_nutrients()
        assert len(nutrients) >= 28

    def test_sorted(self) -> None:
        nutrients = list_nutrients()
        assert nutrients == sorted(nutrients)

    def test_contains_key_nutrients(self) -> None:
        nutrients = set(list_nutrients())
        for n in [
            "calcium",
            "iron",
            "vitamin_c",
            "vitamin_d",
            "zinc",
            "folate",
            "protein",
            "fiber",
        ]:
            assert n in nutrients, f"{n} missing"

    def test_all_nutrients_have_adult_male_entry(self) -> None:
        for nutrient in list_nutrients():
            v = get_dri(nutrient, "adult", "male")
            assert v is not None, f"{nutrient} missing adult/male entry"
            assert isinstance(v, DRIValues)
