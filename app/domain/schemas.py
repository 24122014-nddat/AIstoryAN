from __future__ import annotations

from pydantic import BaseModel, Field
from app.domain.models import Message, SessionState

class StartGameRequest(BaseModel):
    player_name: str = Field(default="Người lữ hành", min_length=1, max_length=80)
    gender: str | None = Field(default=None, max_length=120)
    personality: str | None = Field(default=None, max_length=300)
    story_style: str | None = Field(default=None, max_length=200)
    character_hint: str | None = Field(default=None, max_length=1000)
    world_hint: str | None = Field(default=None, max_length=1000)

class TurnRequest(BaseModel):
    session_id: str
    player_input: str = Field(min_length=1, max_length=4000)
    target_words: int = Field(default=600, ge=100, le=2000)

class StoryResponse(BaseModel):
    session_id: str
    message: str
    choices: list[str] = Field(default_factory=list)
    foundation_text: str = ""
    session: SessionState
    # RPG State (for frontend UI)
    gold: int = 0
    inventory: list = Field(default_factory=list)
    party: list = Field(default_factory=list)

class SessionResponse(BaseModel):
    session: SessionState
    messages: list[Message]
    # RPG State exposed at top level (mirrors StoryResponse) so the
    # frontend can read these without digging into session.*
    gold: int = 0
    inventory: list = Field(default_factory=list)
    party: list = Field(default_factory=list)
class NovelStartRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    world_seed: str | None = Field(default=None, max_length=4000)
    target_words: int = Field(default=600, ge=150, le=2000)


class NovelQuestionAnswer(BaseModel):
    question_id: str
    question: str
    answer: str


class NovelWorldResponse(BaseModel):
    session_id: str
    world_draft: str
    questions: list[dict] = Field(default_factory=list)
    session: SessionState


class NovelFoundationRequest(BaseModel):
    session_id: str
    player_name: str = Field(default="The Wanderer", min_length=1, max_length=80)
    gender: str | None = Field(default=None, max_length=120)
    age: str | None = Field(default=None, max_length=80)
    occupation: str | None = Field(default=None, max_length=160)
    personality: str | None = Field(default=None, max_length=500)
    answers: list[NovelQuestionAnswer] = Field(default_factory=list)
    target_words: int = Field(default=600, ge=150, le=2000)


# ─────────────────────────────────────────────────────────────────────────────
# RPG Transaction Request Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ShopBuyRequest(BaseModel):
    """Purchase one item or one hireable NPC from the active shop grid."""
    session_id: str
    buy_type: str = Field(
        description="'item' to buy from shop_data['items'], 'npc' to hire from shop_data['npcs']"
    )
    index: int = Field(
        ge=0,
        description="Zero-based index inside the shop items or npcs list",
    )


class ShopRefreshRequest(BaseModel):
    """Spend 2 gold to reroll the active shop grid."""
    session_id: str


class UpgradeRequest(BaseModel):
    """Upgrade the merchant stall or the priest shrine."""
    session_id: str
    target: str = Field(
        description="'merchant' to upgrade merchant_level, 'priest' to upgrade priest_level"
    )


class EquipRequest(BaseModel):
    """Move an item from inventory into a character's equipment slot."""
    session_id: str
    char_index: int = Field(ge=0, description="Zero-based index of the party member")
    item_id: str = Field(description="item_id of the InventoryItem to equip")
    slot_type: str = Field(
        description="Target slot: 'weapon', 'armor', or 'consumable'"
    )


class RpgStateResponse(BaseModel):
    """
    Returned by every RPG transaction endpoint.

    Contains only the mutable RPG state so the frontend can patch its local
    copy without a full session reload.
    """
    gold:              int
    merchant_level:    int
    priest_level:      int
    inventory:         list = Field(default_factory=list)
    party:             list = Field(default_factory=list)
    current_shop_data: dict | None = None