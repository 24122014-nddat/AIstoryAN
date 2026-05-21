"""
app/api/rpg_routes.py
=====================
FastAPI router for all synchronous RPG transaction endpoints.

These endpoints perform immediate state mutations (buying, equipping, upgrading)
that do NOT require the LLM.  They are intentionally separate from the story
routes so they can be called at any time without incurring AI latency.

Prefix : /api/rpg
Auth   : Firebase ID token via get_current_user dependency (same as story_routes)
Returns: RpgStateResponse on every success so the frontend can patch its local
         state without a full session reload.
"""

from __future__ import annotations

import random
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.auth.firebase_auth import get_current_user
from app.domain.models import InventoryItem, PartyMember, SessionState, utc_now_iso
from app.domain.rpg_data import ITEM_DATA, generate_npc
from app.domain.schemas import (
    EquipRequest,
    RpgStateResponse,
    ShopBuyRequest,
    ShopRefreshRequest,
    UpgradeRequest,
)
from app.memory.firebase_store import FirebaseStore

router = APIRouter(prefix="/api/rpg", tags=["RPG"])

# ── Shared FirebaseStore instance (stateless – safe to share) ────────────────
_store = FirebaseStore()

# ── Game constants ────────────────────────────────────────────────────────────
# Gold cost to hire one NPC from the shop.
# Items use their own price from ITEM_DATA.
NPC_HIRE_COST: int = 50

# Gold cost to reroll the shop grid.
SHOP_REFRESH_COST: int = 2

# Maximum allowed party size (including the main character).
MAX_PARTY_SIZE: int = 4


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _load_session_for_user(session_id: str, user_uid: str) -> SessionState:
    """
    Load a session from Firebase and verify ownership.

    Raises
    ------
    HTTPException 404  – session not found.
    HTTPException 403  – session belongs to a different user.
    """
    session = await _store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.user_id != user_uid:
        raise HTTPException(status_code=403, detail="You do not own this session.")
    return session


def _rpg_state(session: SessionState) -> RpgStateResponse:
    """Build the standard RpgStateResponse from a session."""
    return RpgStateResponse(
        gold=session.gold,
        merchant_level=session.merchant_level,
        priest_level=session.priest_level,
        inventory=[i.model_dump() for i in session.inventory],
        party=[m.model_dump() for m in session.party],
        current_shop_data=session.current_shop_data,
    )


def _build_shop_data(merchant_level: int) -> dict:
    """
    Generate a fresh shop grid using the same logic as the Event Director.

    Grid size: level 1 → 4 slots, level 2 → 5 slots, level 3+ → 6 slots.
    Items are sampled without replacement; NPCs are freshly gacha-rolled.
    """
    grid_size = 4 if merchant_level == 1 else (5 if merchant_level == 2 else 6)

    shop_items = random.sample(ITEM_DATA, k=min(grid_size, len(ITEM_DATA)))
    shop_npcs  = [generate_npc(merchant_level) for _ in range(grid_size)]

    return {
        "items":           shop_items,
        "npcs":            shop_npcs,
        "merchant_level":  merchant_level,
    }


def _slot_field(slot_type: str) -> str:
    """Map a slot_type string to the PartyMember field name."""
    mapping = {
        "weapon":     "weapon_slot",
        "armor":      "armor_slot",
        "consumable": "consumable_slot",
    }
    if slot_type not in mapping:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid slot_type '{slot_type}'. Must be 'weapon', 'armor', or 'consumable'.",
        )
    return mapping[slot_type]


# ─────────────────────────────────────────────────────────────────────────────
# A. POST /api/rpg/shop/buy
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/shop/buy", response_model=RpgStateResponse)
async def shop_buy(
    request: ShopBuyRequest,
    user=Depends(get_current_user),
) -> RpgStateResponse:
    """
    Purchase one item OR hire one NPC from the currently active shop grid.

    Rules
    -----
    - A shop grid must exist (`current_shop_data` is not None).
    - `buy_type` must be ``"item"`` or ``"npc"``.
    - Items: player must have enough gold (item['price']).
      On success the item is appended to inventory and removed from the grid.
    - NPCs: player must have enough gold (NPC_HIRE_COST) AND party size < 4.
      On success the NPC dict is converted to a PartyMember, appended to the
      party, and removed from the grid.
    """
    if request.buy_type not in {"item", "npc"}:
        raise HTTPException(
            status_code=422,
            detail="buy_type must be 'item' or 'npc'.",
        )

    session = await _load_session_for_user(request.session_id, user["uid"])

    # ── Guard: shop must exist ────────────────────────────────────────────────
    if not session.current_shop_data:
        raise HTTPException(
            status_code=409,
            detail="No active shop. The shop only appears on MERCHANT event turns.",
        )

    shop = session.current_shop_data

    # ── Branch: buy ITEM ─────────────────────────────────────────────────────
    if request.buy_type == "item":
        items: list[dict] = shop.get("items", [])

        if request.index >= len(items):
            raise HTTPException(
                status_code=404,
                detail=f"Item index {request.index} out of range (shop has {len(items)} items).",
            )

        item = items[request.index]
        price: int = item.get("price", 0)

        if session.gold < price:
            raise HTTPException(
                status_code=402,
                detail=f"Not enough gold. Need {price}, have {session.gold}.",
            )

        # Deduct gold
        session.gold -= price

        # Add to inventory (stack if name already present)
        existing = next(
            (i for i in session.inventory if i.name == item["name"]), None
        )
        if existing:
            existing.quantity += 1
        else:
            session.inventory.append(
                InventoryItem(
                    item_id=str(uuid4()),
                    name=item["name"],
                    quantity=1,
                    type=item.get("type", "discovered"),
                )
            )

        # Remove sold item from the shop grid
        items.pop(request.index)
        shop["items"] = items

    # ── Branch: hire NPC ─────────────────────────────────────────────────────
    else:  # buy_type == "npc"
        npcs: list[dict] = shop.get("npcs", [])

        if request.index >= len(npcs):
            raise HTTPException(
                status_code=404,
                detail=f"NPC index {request.index} out of range (shop has {len(npcs)} NPCs).",
            )

        if len(session.party) >= MAX_PARTY_SIZE:
            raise HTTPException(
                status_code=409,
                detail=f"Party is full ({MAX_PARTY_SIZE} members maximum).",
            )

        if session.gold < NPC_HIRE_COST:
            raise HTTPException(
                status_code=402,
                detail=f"Not enough gold to hire NPC. Need {NPC_HIRE_COST}, have {session.gold}.",
            )

        npc_dict = npcs[request.index]

        # Deduct gold
        session.gold -= NPC_HIRE_COST

        # Convert NPC dict → PartyMember (generate_npc() already returns a
        # PartyMember-compatible dict so we can unpack it directly)
        new_member = PartyMember(**npc_dict)
        session.party.append(new_member)

        # Remove hired NPC from the shop grid
        npcs.pop(request.index)
        shop["npcs"] = npcs

    # ── Persist ───────────────────────────────────────────────────────────────
    session.current_shop_data = shop
    session.updated_at = utc_now_iso()
    await _store.update_session(session)

    return _rpg_state(session)


# ─────────────────────────────────────────────────────────────────────────────
# B. POST /api/rpg/shop/refresh
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/shop/refresh", response_model=RpgStateResponse)
async def shop_refresh(
    request: ShopRefreshRequest,
    user=Depends(get_current_user),
) -> RpgStateResponse:
    """
    Spend ``SHOP_REFRESH_COST`` (2) gold to reroll the entire shop grid.

    A shop must already be open (``current_shop_data`` is not None).
    The new grid is generated using the session's current ``merchant_level``
    so upgrades are reflected immediately.
    """
    session = await _load_session_for_user(request.session_id, user["uid"])

    if not session.current_shop_data:
        raise HTTPException(
            status_code=409,
            detail="No active shop to refresh.",
        )

    if session.gold < SHOP_REFRESH_COST:
        raise HTTPException(
            status_code=402,
            detail=f"Not enough gold to refresh the shop. Need {SHOP_REFRESH_COST}, have {session.gold}.",
        )

    session.gold -= SHOP_REFRESH_COST
    session.current_shop_data = _build_shop_data(session.merchant_level)

    session.updated_at = utc_now_iso()
    await _store.update_session(session)

    return _rpg_state(session)


# ─────────────────────────────────────────────────────────────────────────────
# C. POST /api/rpg/upgrade
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/upgrade", response_model=RpgStateResponse)
async def upgrade_facility(
    request: UpgradeRequest,
    user=Depends(get_current_user),
) -> RpgStateResponse:
    """
    Upgrade the merchant stall or the priest shrine.

    Merchant upgrade cost formula : 10 + (current_level - 1) × 5  (cap: level 6)
      level 1 → 2 : 10 gold
      level 2 → 3 : 15 gold
      level 3 → 4 : 20 gold
      level 4 → 5 : 25 gold
      level 5 → 6 : 30 gold

    Priest upgrade cost formula   : current_level × 5              (cap: level 4)
      level 1 → 2 :  5 gold
      level 2 → 3 : 10 gold
      level 3 → 4 : 15 gold
    """
    if request.target not in {"merchant", "priest"}:
        raise HTTPException(
            status_code=422,
            detail="target must be 'merchant' or 'priest'.",
        )

    session = await _load_session_for_user(request.session_id, user["uid"])

    if request.target == "merchant":
        current = session.merchant_level
        cap     = 6
        cost    = 10 + (current - 1) * 5

        if current >= cap:
            raise HTTPException(
                status_code=409,
                detail=f"Merchant is already at maximum level ({cap}).",
            )
        if session.gold < cost:
            raise HTTPException(
                status_code=402,
                detail=f"Not enough gold to upgrade merchant. Need {cost}, have {session.gold}.",
            )

        session.gold -= cost
        session.merchant_level += 1

    else:  # priest
        current = session.priest_level
        cap     = 4
        cost    = current * 5

        if current >= cap:
            raise HTTPException(
                status_code=409,
                detail=f"Priest shrine is already at maximum level ({cap}).",
            )
        if session.gold < cost:
            raise HTTPException(
                status_code=402,
                detail=f"Not enough gold to upgrade priest shrine. Need {cost}, have {session.gold}.",
            )

        session.gold -= cost
        session.priest_level += 1

    session.updated_at = utc_now_iso()
    await _store.update_session(session)

    return _rpg_state(session)


# ─────────────────────────────────────────────────────────────────────────────
# D. POST /api/rpg/equipment/equip
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/equipment/equip", response_model=RpgStateResponse)
async def equip_item(
    request: EquipRequest,
    user=Depends(get_current_user),
) -> RpgStateResponse:
    """
    Move an item from the session inventory into a party member's equipment slot.

    Swap logic
    ----------
    1. Locate the item in ``session.inventory`` by ``item_id``.
    2. Locate the target party member by ``char_index``.
    3. If the target slot is already occupied:
       - move the currently equipped item back to inventory (quantity = 1),
       - then place the new item into the slot.
    4. Remove the new item from inventory (decrement quantity; remove entry if
       quantity reaches 0).

    Only the item snapshot dict is stored in the slot – stat calculation
    (applying bonuses) is deferred to a later step.
    """
    # Validate slot_type and get the PartyMember field name
    slot_field = _slot_field(request.slot_type)

    session = await _load_session_for_user(request.session_id, user["uid"])

    # ── Find the item in inventory ───────────────────────────────────────────
    inv_item: InventoryItem | None = next(
        (i for i in session.inventory if i.item_id == request.item_id), None
    )
    if inv_item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Item '{request.item_id}' not found in inventory.",
        )

    # ── Find the target party member ─────────────────────────────────────────
    if request.char_index >= len(session.party):
        raise HTTPException(
            status_code=404,
            detail=f"Party member at index {request.char_index} does not exist "
                   f"(party has {len(session.party)} members).",
        )

    member: PartyMember = session.party[request.char_index]

    # ── Check if the slot is already occupied ────────────────────────────────
    currently_equipped: dict | None = getattr(member, slot_field)

    if currently_equipped is not None:
        # Move the previously equipped item BACK to inventory
        prev_name = currently_equipped.get("name", "Unknown item")
        prev_type = currently_equipped.get("type", "discovered")

        existing_in_inv = next(
            (i for i in session.inventory if i.name == prev_name), None
        )
        if existing_in_inv:
            existing_in_inv.quantity += 1
        else:
            session.inventory.append(
                InventoryItem(
                    item_id=str(uuid4()),
                    name=prev_name,
                    quantity=1,
                    type=prev_type,
                )
            )

    # ── Build the equipment slot dict from the InventoryItem ─────────────────
    # Store a plain dict snapshot so the slot is self-contained.
    slot_snapshot: dict = {
        "item_id":  inv_item.item_id,
        "name":     inv_item.name,
        "type":     inv_item.type,
    }

    # ── Place item into slot ─────────────────────────────────────────────────
    setattr(member, slot_field, slot_snapshot)

    # ── Remove item from inventory ───────────────────────────────────────────
    inv_item.quantity -= 1
    if inv_item.quantity <= 0:
        session.inventory = [i for i in session.inventory if i.item_id != request.item_id]

    # ── Persist ───────────────────────────────────────────────────────────────
    session.updated_at = utc_now_iso()
    await _store.update_session(session)

    return _rpg_state(session)
