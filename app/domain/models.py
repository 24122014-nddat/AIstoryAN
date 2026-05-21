from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


Role = Literal["user", "ai", "system"]

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class Message(BaseModel):
    message_id: str
    session_id: str
    role: Role
    content: str
    choices: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)

class PartyMember(BaseModel):
    """RPG Party Member model for character tracking"""
    name: str
    class_type: str  # Tanker / Vanguard / Fighter / Caster / Sniper / Medic / Supporter

    # ── Core combat stats ──────────────────────────────────────────
    hp: int
    max_hp: int
    atk: int
    res_atk: int
    atk_def: int
    res_atk_def: int
    atk_spd: int

    # ── Equipment slots (None = slot empty) ───────────────────────
    # Each slot holds a plain dict snapshot from ITEM_DATA when equipped,
    # or None when empty.  Using dict (not InventoryItem) keeps the model
    # self-contained and avoids circular references.
    weapon_slot:     Optional[dict] = None
    armor_slot:      Optional[dict] = None
    consumable_slot: Optional[dict] = None

    # ── NPC metadata ───────────────────────────────────────────────
    # `race`          – canonical race key from RACE_DATA (e.g. "Elf").
    #                   Empty string for the player's main character.
    # `visual_profile` – AI-facing appearance string built by generate_npc().
    # `affinity`      – loyalty/bond score (1-100).
    #                   Main character starts at 100 (always loyal).
    #                   Hired/gacha NPCs start at 50 (must be earned).
    race:           str = ""
    visual_profile: str = ""
    affinity:       int = 100
class InventoryItem(BaseModel):
    """RPG Inventory Item model for resource tracking"""
    item_id: str
    name: str
    quantity: int
    type: str  # e.g., 'weapon', 'armor', 'consumable', 'quest_item'

class SessionState(BaseModel):
    session_id: str
    user_id: str

    title: str = "Cuộc phiêu lưu chưa đặt tên"
    foundation_text: str = ""

    world_summary: str = ""
    character_summary: str = ""
    story_summary: str = ""

    important_facts: list[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    
    mode: Literal["adventure", "novel"] = "adventure"

    world_seed: str = ""
    world_questions: list[dict[str, Any]] = Field(default_factory=list)
    world_answers: list[dict[str, Any]] = Field(default_factory=list)

    novel_profile: dict[str, Any] = Field(default_factory=dict)
    target_words: int = 600

    # ── RPG State Management ───────────────────────────────────────
    gold: int = 0
    item_pity_counter: int = 0
    party: list[PartyMember] = Field(default_factory=list)
    inventory: list[InventoryItem] = Field(default_factory=list)

    # ── Facility levels (isolated per session) ─────────────────────
    # These represent the player's current upgrade tier for each in-world
    # service.  Higher levels unlock better gacha tables (merchant) or
    # stronger healing/buff options (priest).
    merchant_level: int = 1   # 1-6, controls RACE_DATA gacha weights
    priest_level:   int = 1   # 1-6, controls healing pool & options

    # ── Turn-state scratch-pad (written per turn, read by prompt, then cleared) ─
    # These fields hold transient event data produced by the Event Director.
    # They are persisted mid-turn so downstream steps (prompt, future UI) can
    # read them, then set back to None before the next turn begins.
    current_event:     Optional[str]  = None   # e.g. "PRIEST", "MERCHANT", "LOOT"
    current_shop_data: Optional[dict] = None   # populated only on MERCHANT turns
    current_encounter: Optional[dict] = None   # populated only on NPC_ENCOUNTER turns

class MemoryChunk(BaseModel):
    chunk_id: str
    session_id: str
    text: str
    kind: str = "event"
    importance: int = 3
    source_message_id: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)
