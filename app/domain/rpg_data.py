"""
app/domain/rpg_data.py
======================
Read-only Game Data Dictionary for the AI Story RPG system.

This module is the single source of truth for all static game balance values.
It must NOT be mutated at runtime – treat every structure here as a constant.

Contents
--------
RACE_DATA       – Tộc (race) definitions with rarity & allowed classes.
CLASS_DATA      – Nghề nghiệp (class) base statistics & visual descriptions.
ITEM_DATA       – Vật phẩm (item) catalogue with pricing & stat bonuses.
generate_npc()  – 2-step Gacha function that produces a new PartyMember dict.
"""

from __future__ import annotations

import random
from typing import Any

# ═══════════════════════════════════════════════════════════════════
# A. RACE_DATA  – Tộc & Độ hiếm (Race & Rarity)
# ═══════════════════════════════════════════════════════════════════
# Each key is the canonical race name used throughout the system.
# `rarity`         – display tier (Mythical / Legendary / Epic / Rare /
#                    Uncommon / Common).  Also used as the gacha weight key.
# `allowed_classes` – which CLASS_DATA keys this race can combine with.
# `visual_desc`    – short prose fed to the AI for appearance generation.
# ───────────────────────────────────────────────────────────────────
RACE_DATA: dict[str, dict[str, Any]] = {
    "Thánh Kỵ": {
        "rarity": "Mythical",
        "allowed_classes": ["Tanker", "Vanguard", "Fighter", "Caster", "Sniper"],
        "visual_desc": (
            "Hào quang rực rỡ, chiến giáp/vũ khí tinh xảo, nhan sắc cực phẩm."
        ),
    },
    "Thiên Thần/Ác Quỷ": {
        "rarity": "Legendary",
        "allowed_classes": ["Tanker", "Vanguard", "Fighter", "Caster", "Supporter"],
        "visual_desc": (
            "Uy nghi/Hung tợn, cánh ánh sáng/gai góc, sừng, ánh lửa."
        ),
    },
    "Elf": {
        "rarity": "Epic",
        "allowed_classes": ["Fighter", "Caster", "Sniper", "Medic", "Supporter"],
        "visual_desc": (
            "Cánh bươm bướm, tai nhọn, sắc xanh rừng, thanh thoát tao nhã."
        ),
    },
    "Quý Tộc": {
        "rarity": "Rare",
        "allowed_classes": [
            "Tanker", "Vanguard", "Fighter", "Caster",
            "Sniper", "Medic", "Supporter",
        ],
        "visual_desc": (
            "Áo choàng, vương miện, giáp trụ lấp lánh, kiêu sa."
        ),
    },
    "Orc/Goblin": {
        "rarity": "Uncommon",
        "allowed_classes": ["Tanker", "Vanguard", "Fighter", "Caster", "Sniper"],
        "visual_desc": (
            "Da xanh/cam, thấp bé hoặc vạm vỡ, răng nanh, đói khát/tinh ranh."
        ),
    },
    "Thường Dân": {
        "rarity": "Common",
        "allowed_classes": ["Tanker", "Vanguard", "Fighter", "Sniper", "Medic"],
        "visual_desc": (
            "Đồ mộc mạc, nông dân, thợ rèn, giản dị."
        ),
    },
}

# ═══════════════════════════════════════════════════════════════════
# B. CLASS_DATA  – Nghề nghiệp & Chỉ số gốc (Class & Base Stats)
# ═══════════════════════════════════════════════════════════════════
# Base stat layout:
#   atk        – physical attack
#   res_atk    – magical attack
#   def_stat   – physical defence (named `def_stat` to avoid shadowing the
#                built-in `def` keyword)
#   res_def    – magical defence
#   hp         – maximum hit-points
#   atk_speed  – initiative / speed
# ───────────────────────────────────────────────────────────────────
CLASS_DATA: dict[str, dict[str, Any]] = {
    "Tanker": {
        "atk":       10,
        "res_atk":   0,
        "def_stat":  50,
        "res_def":   20,
        "hp":        100,
        "atk_speed": 10,
        "visual_desc": (
            "Leans male. Heavy full-plate armour, tower shield, war-hammer or "
            "longsword. Immovable wall between party and enemies."
        ),
    },
    "Vanguard": {
        "atk":       30,
        "res_atk":   0,
        "def_stat":  30,
        "res_def":   10,
        "hp":        75,
        "atk_speed": 50,
        "visual_desc": (
            "Gender-neutral. Half-armour with mobility cuts, dual blades or "
            "spear. First into the fray, fast and relentless."
        ),
    },
    "Fighter": {
        "atk":       40,
        "res_atk":   10,
        "def_stat":  35,
        "res_def":   10,
        "hp":        65,
        "atk_speed": 30,
        "visual_desc": (
            "Gender-neutral. Battle-worn leather/chain mail, broad sword or "
            "axe. Balanced melee damage and survivability."
        ),
    },
    "Caster": {
        "atk":       5,
        "res_atk":   40,
        "def_stat":  10,
        "res_def":   50,
        "hp":        55,
        "atk_speed": 35,
        "visual_desc": (
            "Leans female. Flowing robes with arcane sigils, magical staff or "
            "grimoire. Devastating spell power, fragile frame."
        ),
    },
    "Sniper": {
        "atk":       50,
        "res_atk":   5,
        "def_stat":  10,
        "res_def":   20,
        "hp":        60,
        "atk_speed": 40,
        "visual_desc": (
            "Gender-neutral. Lightweight scout armour, longbow or crossbow, "
            "keen eyes. Picks targets apart from a safe distance."
        ),
    },
    "Medic": {
        "atk":       0,
        "res_atk":   20,
        "def_stat":  20,
        "res_def":   35,
        "hp":        55,
        "atk_speed": 35,
        "visual_desc": (
            "Leans female. White healer's robes with golden cross motif, "
            "staff with healing orb. Keeps the party alive at all costs."
        ),
    },
    "Supporter": {
        "atk":       5,
        "res_atk":   10,
        "def_stat":  20,
        "res_def":   45,
        "hp":        55,
        "atk_speed": 35,
        "visual_desc": (
            "Gender-neutral. Mid-weight support armour with utility pouches, "
            "wand or enchanted book. Buffs allies and debuffs enemies."
        ),
    },
}

# ═══════════════════════════════════════════════════════════════════
# C. ITEM_DATA  – Vật phẩm & Đánh đổi chỉ số (Item Catalogue)
# ═══════════════════════════════════════════════════════════════════
# Each entry is a plain dict with:
#   id           – unique slug used internally
#   name         – display name (Vietnamese)
#   type         – "weapon" | "armor" | "consumable"
#   price        – gold cost at base merchant
#   stat_bonuses – applied on equip (positive = buff, negative = trade-off)
# Special flags (only on consumables, never in stat_bonuses):
#   is_priest_exclusive  – True  → can only be used by Medic/Priest
#   combat_only          – True  → usable during combat turns only
#   heal_percent         – heal X% of max_hp
#   heal_flat            – heal X flat HP
#   clear_debuffs        – True  → removes all active debuffs on use
# ───────────────────────────────────────────────────────────────────
ITEM_DATA: list[dict[str, Any]] = [
    # ── Weapons ────────────────────────────────────────────────────
    {
        "id": "sword_long",
        "name": "Trường kiếm",
        "type": "weapon",
        "price": 80,
        "stat_bonuses": {
            "atk": 5,
        },
    },
    {
        "id": "shield_iron",
        "name": "Khiên sắt",
        "type": "weapon",          # occupies weapon slot (off-hand)
        "price": 60,
        "stat_bonuses": {
            "def_stat":  10,
            "atk":       -5,
            "atk_speed": -5,
        },
    },
    {
        "id": "staff_magic",
        "name": "Trượng ma pháp",
        "type": "weapon",
        "price": 120,
        "stat_bonuses": {
            "res_atk":   10,
            "atk_speed": -10,
        },
    },
    # ── Armors ─────────────────────────────────────────────────────
    {
        "id": "armor_iron",
        "name": "Giáp sắt",
        "type": "armor",
        "price": 100,
        "stat_bonuses": {
            "def_stat":  10,
            "atk_speed": -5,
        },
    },
    {
        "id": "armor_thorn",
        "name": "Giáp gai",
        "type": "armor",
        "price": 130,
        "stat_bonuses": {
            "atk":    5,
            "def_stat": 5,
            "res_def":  5,
            "hp":    -10,       # trade-off: durability for raw combat power
        },
    },
    {
        "id": "cloak_light",
        "name": "Áo choàng",
        "type": "armor",
        "price": 90,
        "stat_bonuses": {},     # no direct stat deltas
        "dodge_chance": 10,     # special flag: +10% dodge probability
    },
    # ── Consumables ────────────────────────────────────────────────
    {
        "id": "potion_hp_full",
        "name": "Bình HP cấp tốc",
        "type": "consumable",
        "price": 150,
        "stat_bonuses": {},
        "heal_percent":        100,    # restore 100% max_hp
        "is_priest_exclusive": True,   # Medic/Priest only
    },
    {
        "id": "holy_water",
        "name": "Nước thánh",
        "type": "consumable",
        "price": 120,
        "stat_bonuses": {},
        "clear_debuffs":       True,   # purge all active debuffs
        "is_priest_exclusive": True,
    },
    {
        "id": "bandage",
        "name": "Băng gạc",
        "type": "consumable",
        "price": 30,
        "stat_bonuses": {},
        "heal_flat":    10,    # restore 10 flat HP
        "combat_only":  True,  # can only be used mid-combat
    },
]

# Convenience lookup: item by id (O(1) access)
ITEM_BY_ID: dict[str, dict[str, Any]] = {item["id"]: item for item in ITEM_DATA}

# ═══════════════════════════════════════════════════════════════════
# D. GACHA TABLES  – Shop-level probability weights
# ═══════════════════════════════════════════════════════════════════
# Each row maps to one shop level.  Values are integer weights (sum = 100)
# in the order: [Mythical, Legendary, Epic, Rare, Uncommon, Common].
# Levels 1-3 share the same distribution (index 0).
_RACE_ORDER: list[str] = [
    "Thánh Kỵ",          # Mythical
    "Thiên Thần/Ác Quỷ", # Legendary
    "Elf",               # Epic
    "Quý Tộc",           # Rare
    "Orc/Goblin",        # Uncommon
    "Thường Dân",        # Common
]

# Index 0 → shop_level 1-3   (weights must sum to 100)
# Index 1 → shop_level 4
# Index 2 → shop_level 5
# Index 3 → shop_level 6
_GACHA_WEIGHTS: list[list[int]] = [
    # Myth  Leg  Epic  Rare  Uncom  Com
    [  2,    5,   10,   15,   25,   43 ],  # level 1-3
    [  5,    8,   13,   18,   28,   28 ],  # level 4
    [  8,   11,   15,   21,   31,   14 ],  # level 5
    [ 10,   15,   20,   25,   20,   10 ],  # level 6
]


def _weights_for_level(shop_level: int) -> list[int]:
    """Return the correct weight list for a given shop level (1-6+)."""
    if shop_level <= 3:
        return _GACHA_WEIGHTS[0]
    elif shop_level == 4:
        return _GACHA_WEIGHTS[1]
    elif shop_level == 5:
        return _GACHA_WEIGHTS[2]
    else:
        # level 6+ use the top-tier table
        return _GACHA_WEIGHTS[3]


# ═══════════════════════════════════════════════════════════════════
# D. generate_npc()  – 2-step Gacha NPC Factory
# ═══════════════════════════════════════════════════════════════════
def generate_npc(shop_level: int = 1) -> dict[str, Any]:
    """
    Generate a randomised NPC party member using a 2-step Gacha roll.

    Step 1 – Roll Race
    ------------------
    Use `shop_level` to select the correct probability table, then perform
    a weighted random draw from the six races.

    Step 2 – Roll Class
    -------------------
    Filter CLASS_DATA to the classes allowed by the drawn race, then pick
    one uniformly at random.

    Returns a dict compatible with the `PartyMember` Pydantic model
    (all required fields present, plus the new NPC-specific metadata fields).

    Parameters
    ----------
    shop_level : int
        Current merchant level (1–6+).  Controls rarity weights.

    Returns
    -------
    dict
        A dict that can be unpacked into a PartyMember(**result).
    """
    # ── Step 1: Race roll ──────────────────────────────────────────
    weights = _weights_for_level(shop_level)
    [rolled_race] = random.choices(_RACE_ORDER, weights=weights, k=1)
    race_info = RACE_DATA[rolled_race]

    # ── Step 2: Class roll ─────────────────────────────────────────
    eligible_classes = [
        cls for cls in race_info["allowed_classes"] if cls in CLASS_DATA
    ]
    if not eligible_classes:
        # Defensive fallback – should never happen with correct RACE_DATA
        eligible_classes = list(CLASS_DATA.keys())

    rolled_class = random.choice(eligible_classes)
    class_info = CLASS_DATA[rolled_class]

    # ── Build visual profile string ────────────────────────────────
    visual_profile = (
        f"[{race_info['rarity']} · {rolled_race}] {race_info['visual_desc']} "
        f"| [{rolled_class}] {class_info['visual_desc']}"
    )

    # ── Assemble PartyMember-compatible dict ───────────────────────
    # Base stats come directly from CLASS_DATA.
    # `max_hp` mirrors `hp` at creation (modified later by equipment/events).
    # Equipment slots default to None (empty) for a freshly rolled NPC.
    # `affinity` starts at 50 for a hired/gacha NPC (not 100 like the main
    # character who is always loyal).
    return {
        "name":          f"NPC_{rolled_race}_{rolled_class}",  # caller should rename
        "class_type":    rolled_class,
        "race":          rolled_race,
        "visual_profile": visual_profile,
        "affinity":      50,            # NPC default — must be earned
        # Core stats (map CLASS_DATA keys → PartyMember field names)
        "hp":            class_info["hp"],
        "max_hp":        class_info["hp"],
        "atk":           class_info["atk"],
        "res_atk":       class_info["res_atk"],
        "atk_def":       class_info["def_stat"],     # field alias in PartyMember
        "res_atk_def":   class_info["res_def"],      # field alias in PartyMember
        "atk_spd":       class_info["atk_speed"],    # field alias in PartyMember
        # Equipment slots (empty at spawn)
        "weapon_slot":      None,
        "armor_slot":       None,
        "consumable_slot":  None,
    }
