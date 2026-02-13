from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DRIValues:
    """Dietary Reference Intake values for a nutrient.

    Source: National Academies of Sciences, Engineering, and Medicine DRI tables.
    """

    ear: float | None  # Estimated Average Requirement
    rda: float | None  # Recommended Dietary Allowance
    ai: float | None  # Adequate Intake (when RDA not established)
    ul: float | None  # Tolerable Upper Intake Level
    unit: str


# National Academies DRI tables (adults 19-50 unless noted).
# Keys: lowercase nutrient name with underscores.
# Structure: {nutrient: {(age_group, sex): DRIValues}}
# age_group: "infant", "child", "teen", "adult", "elderly", "pregnant", "lactating"
# sex: "male", "female"

_DRI_DATA: dict[str, dict[tuple[str, str], DRIValues]] = {
    "vitamin_a": {
        ("adult", "male"): DRIValues(ear=625, rda=900, ai=None, ul=3000, unit="mcg_rae"),
        ("adult", "female"): DRIValues(ear=500, rda=700, ai=None, ul=3000, unit="mcg_rae"),
        ("child", "male"): DRIValues(ear=275, rda=400, ai=None, ul=900, unit="mcg_rae"),
        ("child", "female"): DRIValues(ear=275, rda=400, ai=None, ul=900, unit="mcg_rae"),
        ("teen", "male"): DRIValues(ear=630, rda=900, ai=None, ul=2800, unit="mcg_rae"),
        ("teen", "female"): DRIValues(ear=485, rda=700, ai=None, ul=2800, unit="mcg_rae"),
        ("elderly", "male"): DRIValues(ear=625, rda=900, ai=None, ul=3000, unit="mcg_rae"),
        ("elderly", "female"): DRIValues(ear=500, rda=700, ai=None, ul=3000, unit="mcg_rae"),
        ("pregnant", "female"): DRIValues(ear=550, rda=770, ai=None, ul=3000, unit="mcg_rae"),
        ("lactating", "female"): DRIValues(ear=900, rda=1300, ai=None, ul=3000, unit="mcg_rae"),
    },
    "vitamin_c": {
        ("adult", "male"): DRIValues(ear=75, rda=90, ai=None, ul=2000, unit="mg"),
        ("adult", "female"): DRIValues(ear=60, rda=75, ai=None, ul=2000, unit="mg"),
        ("child", "male"): DRIValues(ear=22, rda=25, ai=None, ul=650, unit="mg"),
        ("child", "female"): DRIValues(ear=22, rda=25, ai=None, ul=650, unit="mg"),
        ("teen", "male"): DRIValues(ear=63, rda=75, ai=None, ul=1800, unit="mg"),
        ("teen", "female"): DRIValues(ear=56, rda=65, ai=None, ul=1800, unit="mg"),
        ("elderly", "male"): DRIValues(ear=75, rda=90, ai=None, ul=2000, unit="mg"),
        ("elderly", "female"): DRIValues(ear=60, rda=75, ai=None, ul=2000, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=70, rda=85, ai=None, ul=2000, unit="mg"),
        ("lactating", "female"): DRIValues(ear=100, rda=120, ai=None, ul=2000, unit="mg"),
    },
    "vitamin_d": {
        ("adult", "male"): DRIValues(ear=10, rda=15, ai=None, ul=100, unit="mcg"),
        ("adult", "female"): DRIValues(ear=10, rda=15, ai=None, ul=100, unit="mcg"),
        ("child", "male"): DRIValues(ear=10, rda=15, ai=None, ul=75, unit="mcg"),
        ("child", "female"): DRIValues(ear=10, rda=15, ai=None, ul=75, unit="mcg"),
        ("teen", "male"): DRIValues(ear=10, rda=15, ai=None, ul=100, unit="mcg"),
        ("teen", "female"): DRIValues(ear=10, rda=15, ai=None, ul=100, unit="mcg"),
        ("elderly", "male"): DRIValues(ear=10, rda=20, ai=None, ul=100, unit="mcg"),
        ("elderly", "female"): DRIValues(ear=10, rda=20, ai=None, ul=100, unit="mcg"),
        ("pregnant", "female"): DRIValues(ear=10, rda=15, ai=None, ul=100, unit="mcg"),
        ("lactating", "female"): DRIValues(ear=10, rda=15, ai=None, ul=100, unit="mcg"),
    },
    "vitamin_e": {
        ("adult", "male"): DRIValues(ear=12, rda=15, ai=None, ul=1000, unit="mg"),
        ("adult", "female"): DRIValues(ear=12, rda=15, ai=None, ul=1000, unit="mg"),
        ("child", "male"): DRIValues(ear=5, rda=7, ai=None, ul=300, unit="mg"),
        ("child", "female"): DRIValues(ear=5, rda=7, ai=None, ul=300, unit="mg"),
        ("teen", "male"): DRIValues(ear=12, rda=15, ai=None, ul=800, unit="mg"),
        ("teen", "female"): DRIValues(ear=12, rda=15, ai=None, ul=800, unit="mg"),
        ("elderly", "male"): DRIValues(ear=12, rda=15, ai=None, ul=1000, unit="mg"),
        ("elderly", "female"): DRIValues(ear=12, rda=15, ai=None, ul=1000, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=12, rda=15, ai=None, ul=1000, unit="mg"),
        ("lactating", "female"): DRIValues(ear=16, rda=19, ai=None, ul=1000, unit="mg"),
    },
    "vitamin_k": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=120, ul=None, unit="mcg"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=90, ul=None, unit="mcg"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=55, ul=None, unit="mcg"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=55, ul=None, unit="mcg"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=75, ul=None, unit="mcg"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=75, ul=None, unit="mcg"),
        ("elderly", "male"): DRIValues(ear=None, rda=None, ai=120, ul=None, unit="mcg"),
        ("elderly", "female"): DRIValues(ear=None, rda=None, ai=90, ul=None, unit="mcg"),
        ("pregnant", "female"): DRIValues(ear=None, rda=None, ai=90, ul=None, unit="mcg"),
        ("lactating", "female"): DRIValues(ear=None, rda=None, ai=90, ul=None, unit="mcg"),
    },
    "thiamin": {
        ("adult", "male"): DRIValues(ear=1.0, rda=1.2, ai=None, ul=None, unit="mg"),
        ("adult", "female"): DRIValues(ear=0.9, rda=1.1, ai=None, ul=None, unit="mg"),
        ("child", "male"): DRIValues(ear=0.5, rda=0.6, ai=None, ul=None, unit="mg"),
        ("child", "female"): DRIValues(ear=0.5, rda=0.6, ai=None, ul=None, unit="mg"),
        ("teen", "male"): DRIValues(ear=1.0, rda=1.2, ai=None, ul=None, unit="mg"),
        ("teen", "female"): DRIValues(ear=0.9, rda=1.0, ai=None, ul=None, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=1.2, rda=1.4, ai=None, ul=None, unit="mg"),
        ("lactating", "female"): DRIValues(ear=1.2, rda=1.4, ai=None, ul=None, unit="mg"),
    },
    "riboflavin": {
        ("adult", "male"): DRIValues(ear=1.1, rda=1.3, ai=None, ul=None, unit="mg"),
        ("adult", "female"): DRIValues(ear=0.9, rda=1.1, ai=None, ul=None, unit="mg"),
        ("child", "male"): DRIValues(ear=0.5, rda=0.6, ai=None, ul=None, unit="mg"),
        ("child", "female"): DRIValues(ear=0.5, rda=0.6, ai=None, ul=None, unit="mg"),
        ("teen", "male"): DRIValues(ear=1.1, rda=1.3, ai=None, ul=None, unit="mg"),
        ("teen", "female"): DRIValues(ear=0.9, rda=1.0, ai=None, ul=None, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=1.2, rda=1.4, ai=None, ul=None, unit="mg"),
        ("lactating", "female"): DRIValues(ear=1.3, rda=1.6, ai=None, ul=None, unit="mg"),
    },
    "niacin": {
        ("adult", "male"): DRIValues(ear=12, rda=16, ai=None, ul=35, unit="mg"),
        ("adult", "female"): DRIValues(ear=11, rda=14, ai=None, ul=35, unit="mg"),
        ("child", "male"): DRIValues(ear=6, rda=8, ai=None, ul=15, unit="mg"),
        ("child", "female"): DRIValues(ear=6, rda=8, ai=None, ul=15, unit="mg"),
        ("teen", "male"): DRIValues(ear=12, rda=16, ai=None, ul=30, unit="mg"),
        ("teen", "female"): DRIValues(ear=11, rda=14, ai=None, ul=30, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=14, rda=18, ai=None, ul=35, unit="mg"),
        ("lactating", "female"): DRIValues(ear=13, rda=17, ai=None, ul=35, unit="mg"),
    },
    "pantothenic_acid": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=5, ul=None, unit="mg"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=5, ul=None, unit="mg"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=3, ul=None, unit="mg"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=3, ul=None, unit="mg"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=5, ul=None, unit="mg"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=5, ul=None, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=None, rda=None, ai=6, ul=None, unit="mg"),
        ("lactating", "female"): DRIValues(ear=None, rda=None, ai=7, ul=None, unit="mg"),
    },
    "vitamin_b6": {
        ("adult", "male"): DRIValues(ear=1.1, rda=1.3, ai=None, ul=100, unit="mg"),
        ("adult", "female"): DRIValues(ear=1.1, rda=1.3, ai=None, ul=100, unit="mg"),
        ("child", "male"): DRIValues(ear=0.5, rda=0.6, ai=None, ul=40, unit="mg"),
        ("child", "female"): DRIValues(ear=0.5, rda=0.6, ai=None, ul=40, unit="mg"),
        ("teen", "male"): DRIValues(ear=1.1, rda=1.3, ai=None, ul=80, unit="mg"),
        ("teen", "female"): DRIValues(ear=1.0, rda=1.2, ai=None, ul=80, unit="mg"),
        ("elderly", "male"): DRIValues(ear=1.4, rda=1.7, ai=None, ul=100, unit="mg"),
        ("elderly", "female"): DRIValues(ear=1.3, rda=1.5, ai=None, ul=100, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=1.6, rda=1.9, ai=None, ul=100, unit="mg"),
        ("lactating", "female"): DRIValues(ear=1.7, rda=2.0, ai=None, ul=100, unit="mg"),
    },
    "biotin": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=30, ul=None, unit="mcg"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=30, ul=None, unit="mcg"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=12, ul=None, unit="mcg"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=12, ul=None, unit="mcg"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=25, ul=None, unit="mcg"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=25, ul=None, unit="mcg"),
        ("pregnant", "female"): DRIValues(ear=None, rda=None, ai=30, ul=None, unit="mcg"),
        ("lactating", "female"): DRIValues(ear=None, rda=None, ai=35, ul=None, unit="mcg"),
    },
    "folate": {
        ("adult", "male"): DRIValues(ear=320, rda=400, ai=None, ul=1000, unit="mcg_dfe"),
        ("adult", "female"): DRIValues(ear=320, rda=400, ai=None, ul=1000, unit="mcg_dfe"),
        ("child", "male"): DRIValues(ear=160, rda=200, ai=None, ul=400, unit="mcg_dfe"),
        ("child", "female"): DRIValues(ear=160, rda=200, ai=None, ul=400, unit="mcg_dfe"),
        ("teen", "male"): DRIValues(ear=330, rda=400, ai=None, ul=800, unit="mcg_dfe"),
        ("teen", "female"): DRIValues(ear=330, rda=400, ai=None, ul=800, unit="mcg_dfe"),
        ("pregnant", "female"): DRIValues(ear=520, rda=600, ai=None, ul=1000, unit="mcg_dfe"),
        ("lactating", "female"): DRIValues(ear=450, rda=500, ai=None, ul=1000, unit="mcg_dfe"),
    },
    "vitamin_b12": {
        ("adult", "male"): DRIValues(ear=2.0, rda=2.4, ai=None, ul=None, unit="mcg"),
        ("adult", "female"): DRIValues(ear=2.0, rda=2.4, ai=None, ul=None, unit="mcg"),
        ("child", "male"): DRIValues(ear=1.0, rda=1.2, ai=None, ul=None, unit="mcg"),
        ("child", "female"): DRIValues(ear=1.0, rda=1.2, ai=None, ul=None, unit="mcg"),
        ("teen", "male"): DRIValues(ear=2.0, rda=2.4, ai=None, ul=None, unit="mcg"),
        ("teen", "female"): DRIValues(ear=2.0, rda=2.4, ai=None, ul=None, unit="mcg"),
        ("pregnant", "female"): DRIValues(ear=2.2, rda=2.6, ai=None, ul=None, unit="mcg"),
        ("lactating", "female"): DRIValues(ear=2.4, rda=2.8, ai=None, ul=None, unit="mcg"),
    },
    "calcium": {
        ("adult", "male"): DRIValues(ear=800, rda=1000, ai=None, ul=2500, unit="mg"),
        ("adult", "female"): DRIValues(ear=800, rda=1000, ai=None, ul=2500, unit="mg"),
        ("child", "male"): DRIValues(ear=800, rda=1000, ai=None, ul=2500, unit="mg"),
        ("child", "female"): DRIValues(ear=800, rda=1000, ai=None, ul=2500, unit="mg"),
        ("teen", "male"): DRIValues(ear=1100, rda=1300, ai=None, ul=3000, unit="mg"),
        ("teen", "female"): DRIValues(ear=1100, rda=1300, ai=None, ul=3000, unit="mg"),
        ("elderly", "male"): DRIValues(ear=800, rda=1000, ai=None, ul=2000, unit="mg"),
        ("elderly", "female"): DRIValues(ear=1000, rda=1200, ai=None, ul=2000, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=800, rda=1000, ai=None, ul=2500, unit="mg"),
        ("lactating", "female"): DRIValues(ear=800, rda=1000, ai=None, ul=2500, unit="mg"),
    },
    "iron": {
        ("adult", "male"): DRIValues(ear=6, rda=8, ai=None, ul=45, unit="mg"),
        ("adult", "female"): DRIValues(ear=8.1, rda=18, ai=None, ul=45, unit="mg"),
        ("child", "male"): DRIValues(ear=4.1, rda=10, ai=None, ul=40, unit="mg"),
        ("child", "female"): DRIValues(ear=4.1, rda=10, ai=None, ul=40, unit="mg"),
        ("teen", "male"): DRIValues(ear=7.7, rda=11, ai=None, ul=45, unit="mg"),
        ("teen", "female"): DRIValues(ear=7.9, rda=15, ai=None, ul=45, unit="mg"),
        ("elderly", "male"): DRIValues(ear=6, rda=8, ai=None, ul=45, unit="mg"),
        ("elderly", "female"): DRIValues(ear=5, rda=8, ai=None, ul=45, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=22, rda=27, ai=None, ul=45, unit="mg"),
        ("lactating", "female"): DRIValues(ear=6.5, rda=9, ai=None, ul=45, unit="mg"),
    },
    "magnesium": {
        ("adult", "male"): DRIValues(ear=330, rda=400, ai=None, ul=350, unit="mg"),
        ("adult", "female"): DRIValues(ear=255, rda=310, ai=None, ul=350, unit="mg"),
        ("child", "male"): DRIValues(ear=110, rda=130, ai=None, ul=110, unit="mg"),
        ("child", "female"): DRIValues(ear=110, rda=130, ai=None, ul=110, unit="mg"),
        ("teen", "male"): DRIValues(ear=340, rda=410, ai=None, ul=350, unit="mg"),
        ("teen", "female"): DRIValues(ear=300, rda=360, ai=None, ul=350, unit="mg"),
        ("elderly", "male"): DRIValues(ear=350, rda=420, ai=None, ul=350, unit="mg"),
        ("elderly", "female"): DRIValues(ear=265, rda=320, ai=None, ul=350, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=290, rda=350, ai=None, ul=350, unit="mg"),
        ("lactating", "female"): DRIValues(ear=255, rda=310, ai=None, ul=350, unit="mg"),
    },
    "zinc": {
        ("adult", "male"): DRIValues(ear=9.4, rda=11, ai=None, ul=40, unit="mg"),
        ("adult", "female"): DRIValues(ear=6.8, rda=8, ai=None, ul=40, unit="mg"),
        ("child", "male"): DRIValues(ear=4.0, rda=5, ai=None, ul=12, unit="mg"),
        ("child", "female"): DRIValues(ear=4.0, rda=5, ai=None, ul=12, unit="mg"),
        ("teen", "male"): DRIValues(ear=8.5, rda=11, ai=None, ul=34, unit="mg"),
        ("teen", "female"): DRIValues(ear=7.3, rda=9, ai=None, ul=34, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=9.5, rda=11, ai=None, ul=40, unit="mg"),
        ("lactating", "female"): DRIValues(ear=10.4, rda=12, ai=None, ul=40, unit="mg"),
    },
    "copper": {
        ("adult", "male"): DRIValues(ear=700, rda=900, ai=None, ul=10000, unit="mcg"),
        ("adult", "female"): DRIValues(ear=700, rda=900, ai=None, ul=10000, unit="mcg"),
        ("child", "male"): DRIValues(ear=340, rda=440, ai=None, ul=3000, unit="mcg"),
        ("child", "female"): DRIValues(ear=340, rda=440, ai=None, ul=3000, unit="mcg"),
        ("teen", "male"): DRIValues(ear=685, rda=890, ai=None, ul=8000, unit="mcg"),
        ("teen", "female"): DRIValues(ear=685, rda=890, ai=None, ul=8000, unit="mcg"),
        ("pregnant", "female"): DRIValues(ear=800, rda=1000, ai=None, ul=10000, unit="mcg"),
        ("lactating", "female"): DRIValues(ear=1000, rda=1300, ai=None, ul=10000, unit="mcg"),
    },
    "selenium": {
        ("adult", "male"): DRIValues(ear=45, rda=55, ai=None, ul=400, unit="mcg"),
        ("adult", "female"): DRIValues(ear=45, rda=55, ai=None, ul=400, unit="mcg"),
        ("child", "male"): DRIValues(ear=23, rda=30, ai=None, ul=150, unit="mcg"),
        ("child", "female"): DRIValues(ear=23, rda=30, ai=None, ul=150, unit="mcg"),
        ("teen", "male"): DRIValues(ear=45, rda=55, ai=None, ul=400, unit="mcg"),
        ("teen", "female"): DRIValues(ear=45, rda=55, ai=None, ul=400, unit="mcg"),
        ("pregnant", "female"): DRIValues(ear=49, rda=60, ai=None, ul=400, unit="mcg"),
        ("lactating", "female"): DRIValues(ear=59, rda=70, ai=None, ul=400, unit="mcg"),
    },
    "phosphorus": {
        ("adult", "male"): DRIValues(ear=580, rda=700, ai=None, ul=4000, unit="mg"),
        ("adult", "female"): DRIValues(ear=580, rda=700, ai=None, ul=4000, unit="mg"),
        ("child", "male"): DRIValues(ear=405, rda=500, ai=None, ul=3000, unit="mg"),
        ("child", "female"): DRIValues(ear=405, rda=500, ai=None, ul=3000, unit="mg"),
        ("teen", "male"): DRIValues(ear=1055, rda=1250, ai=None, ul=4000, unit="mg"),
        ("teen", "female"): DRIValues(ear=1055, rda=1250, ai=None, ul=4000, unit="mg"),
        ("elderly", "male"): DRIValues(ear=580, rda=700, ai=None, ul=4000, unit="mg"),
        ("elderly", "female"): DRIValues(ear=580, rda=700, ai=None, ul=3000, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=580, rda=700, ai=None, ul=3500, unit="mg"),
        ("lactating", "female"): DRIValues(ear=580, rda=700, ai=None, ul=4000, unit="mg"),
    },
    "potassium": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=3400, ul=None, unit="mg"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=2600, ul=None, unit="mg"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=2300, ul=None, unit="mg"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=2300, ul=None, unit="mg"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=3000, ul=None, unit="mg"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=2300, ul=None, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=None, rda=None, ai=2900, ul=None, unit="mg"),
        ("lactating", "female"): DRIValues(ear=None, rda=None, ai=2800, ul=None, unit="mg"),
    },
    "sodium": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=1500, ul=2300, unit="mg"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=1500, ul=2300, unit="mg"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=1200, ul=1900, unit="mg"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=1200, ul=1900, unit="mg"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=1500, ul=2300, unit="mg"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=1500, ul=2300, unit="mg"),
        ("elderly", "male"): DRIValues(ear=None, rda=None, ai=1500, ul=2300, unit="mg"),
        ("elderly", "female"): DRIValues(ear=None, rda=None, ai=1500, ul=2300, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=None, rda=None, ai=1500, ul=2300, unit="mg"),
        ("lactating", "female"): DRIValues(ear=None, rda=None, ai=1500, ul=2300, unit="mg"),
    },
    "manganese": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=2.3, ul=11, unit="mg"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=1.8, ul=11, unit="mg"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=1.5, ul=3, unit="mg"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=1.5, ul=3, unit="mg"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=2.2, ul=9, unit="mg"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=1.6, ul=9, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=None, rda=None, ai=2.0, ul=11, unit="mg"),
        ("lactating", "female"): DRIValues(ear=None, rda=None, ai=2.6, ul=11, unit="mg"),
    },
    "chromium": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=35, ul=None, unit="mcg"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=25, ul=None, unit="mcg"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=15, ul=None, unit="mcg"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=15, ul=None, unit="mcg"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=35, ul=None, unit="mcg"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=24, ul=None, unit="mcg"),
        ("pregnant", "female"): DRIValues(ear=None, rda=None, ai=30, ul=None, unit="mcg"),
        ("lactating", "female"): DRIValues(ear=None, rda=None, ai=45, ul=None, unit="mcg"),
    },
    "molybdenum": {
        ("adult", "male"): DRIValues(ear=34, rda=45, ai=None, ul=2000, unit="mcg"),
        ("adult", "female"): DRIValues(ear=34, rda=45, ai=None, ul=2000, unit="mcg"),
        ("child", "male"): DRIValues(ear=17, rda=22, ai=None, ul=600, unit="mcg"),
        ("child", "female"): DRIValues(ear=17, rda=22, ai=None, ul=600, unit="mcg"),
        ("teen", "male"): DRIValues(ear=33, rda=43, ai=None, ul=1700, unit="mcg"),
        ("teen", "female"): DRIValues(ear=33, rda=43, ai=None, ul=1700, unit="mcg"),
        ("pregnant", "female"): DRIValues(ear=40, rda=50, ai=None, ul=2000, unit="mcg"),
        ("lactating", "female"): DRIValues(ear=40, rda=50, ai=None, ul=2000, unit="mcg"),
    },
    "iodine": {
        ("adult", "male"): DRIValues(ear=95, rda=150, ai=None, ul=1100, unit="mcg"),
        ("adult", "female"): DRIValues(ear=95, rda=150, ai=None, ul=1100, unit="mcg"),
        ("child", "male"): DRIValues(ear=65, rda=90, ai=None, ul=600, unit="mcg"),
        ("child", "female"): DRIValues(ear=65, rda=90, ai=None, ul=600, unit="mcg"),
        ("teen", "male"): DRIValues(ear=73, rda=120, ai=None, ul=900, unit="mcg"),
        ("teen", "female"): DRIValues(ear=73, rda=120, ai=None, ul=900, unit="mcg"),
        ("pregnant", "female"): DRIValues(ear=160, rda=220, ai=None, ul=1100, unit="mcg"),
        ("lactating", "female"): DRIValues(ear=209, rda=290, ai=None, ul=1100, unit="mcg"),
    },
    "fluoride": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=4, ul=10, unit="mg"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=3, ul=10, unit="mg"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=1, ul=2.2, unit="mg"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=1, ul=2.2, unit="mg"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=3, ul=10, unit="mg"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=3, ul=10, unit="mg"),
    },
    "choline": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=550, ul=3500, unit="mg"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=425, ul=3500, unit="mg"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=250, ul=1000, unit="mg"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=250, ul=1000, unit="mg"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=550, ul=3000, unit="mg"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=400, ul=3000, unit="mg"),
        ("pregnant", "female"): DRIValues(ear=None, rda=None, ai=450, ul=3500, unit="mg"),
        ("lactating", "female"): DRIValues(ear=None, rda=None, ai=550, ul=3500, unit="mg"),
    },
    "fiber": {
        ("adult", "male"): DRIValues(ear=None, rda=None, ai=38, ul=None, unit="g"),
        ("adult", "female"): DRIValues(ear=None, rda=None, ai=25, ul=None, unit="g"),
        ("child", "male"): DRIValues(ear=None, rda=None, ai=25, ul=None, unit="g"),
        ("child", "female"): DRIValues(ear=None, rda=None, ai=25, ul=None, unit="g"),
        ("teen", "male"): DRIValues(ear=None, rda=None, ai=38, ul=None, unit="g"),
        ("teen", "female"): DRIValues(ear=None, rda=None, ai=26, ul=None, unit="g"),
        ("elderly", "male"): DRIValues(ear=None, rda=None, ai=30, ul=None, unit="g"),
        ("elderly", "female"): DRIValues(ear=None, rda=None, ai=21, ul=None, unit="g"),
        ("pregnant", "female"): DRIValues(ear=None, rda=None, ai=28, ul=None, unit="g"),
        ("lactating", "female"): DRIValues(ear=None, rda=None, ai=29, ul=None, unit="g"),
    },
    "protein": {
        ("adult", "male"): DRIValues(ear=0.66, rda=0.8, ai=None, ul=None, unit="g/kg"),
        ("adult", "female"): DRIValues(ear=0.66, rda=0.8, ai=None, ul=None, unit="g/kg"),
        ("child", "male"): DRIValues(ear=0.76, rda=0.95, ai=None, ul=None, unit="g/kg"),
        ("child", "female"): DRIValues(ear=0.76, rda=0.95, ai=None, ul=None, unit="g/kg"),
        ("teen", "male"): DRIValues(ear=0.73, rda=0.85, ai=None, ul=None, unit="g/kg"),
        ("teen", "female"): DRIValues(ear=0.71, rda=0.85, ai=None, ul=None, unit="g/kg"),
        ("pregnant", "female"): DRIValues(ear=0.88, rda=1.1, ai=None, ul=None, unit="g/kg"),
        ("lactating", "female"): DRIValues(ear=1.05, rda=1.3, ai=None, ul=None, unit="g/kg"),
    },
}


def get_dri(nutrient: str, age_group: str = "adult", sex: str = "male") -> DRIValues | None:
    """Look up DRI values for a nutrient by age group and sex."""
    nutrient_data = _DRI_DATA.get(nutrient.lower().replace(" ", "_"))
    if not nutrient_data:
        return None
    return (
        nutrient_data.get((age_group, sex))
        or nutrient_data.get(("adult", sex))
        or nutrient_data.get(("adult", "male"))
    )


def list_nutrients() -> list[str]:
    """Return all nutrients with DRI data."""
    return sorted(_DRI_DATA.keys())
