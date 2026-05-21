from __future__ import annotations

from uuid import uuid4
import random
from app.ai.output_parser import parse_story_output
from app.ai.prompt import (
    build_start_prompt,
    build_turn_prompt,
    build_novel_world_prompt,
    build_novel_foundation_prompt,
)
from app.ai.provider import get_text_provider
from app.domain.models import Message, SessionState, utc_now_iso, PartyMember, InventoryItem
from app.domain.rpg_data import ITEM_DATA, ITEM_BY_ID, generate_npc
from app.domain.schemas import (
    StartGameRequest,
    StoryResponse,
    TurnRequest,
    NovelStartRequest,
    NovelWorldResponse,
    NovelFoundationRequest,
)
from app.memory.firebase_store import FirebaseStore
from app.memory.memory_service import MemoryService
from app.memory.vector_store import VectorStore
from app.services.combat_engine import calculate_exchange
import json
class StoryService:
    def __init__(self) -> None:
        self.provider = get_text_provider()
        self.store = FirebaseStore()
        self.vector_store = VectorStore()
        self.memory = MemoryService(self.store, self.vector_store, self.provider)

    async def start_game(self, request: StartGameRequest, user_id: str,) -> StoryResponse:
        session = SessionState(
            session_id=str(uuid4()),
            user_id=user_id,
            title=f"Câu chuyện của {request.player_name}",
        )
        
        # Initialize RPG state: Add main character to party with base stats
        main_character = PartyMember(
            name=request.player_name,
            class_type="Unknown",  # Default class
            hp=100,
            max_hp=80,
            atk=15,
            atk_def=10,
            res_atk=10,
            res_atk_def=5,
            atk_spd=30,
        )
        session.party.append(main_character)
        session.gold = 0  # Starting gold
        session.item_pity_counter = 0
        
        await self.store.create_session(session)

        prompt = build_start_prompt(
            player_name=request.player_name,
            story_style=request.story_style,
            character_hint=request.character_hint,
            world_hint=request.world_hint,
            gender=request.gender,
            personality=request.personality,
        )

        raw = await self.provider.generate_text(prompt)
        parsed = parse_story_output(raw)

        foundation_text = parsed["foundation"]
        ai_text = parsed["story"]
        choices = parsed["choices"]

        if foundation_text:
            session.foundation_text = foundation_text
            session.world_summary = foundation_text
            session.character_summary = foundation_text
            session.story_summary = "The story has just begun."
            session.important_facts = list(dict.fromkeys(session.important_facts + [foundation_text]))[-12:]
            session.updated_at = utc_now_iso()
            await self.store.update_session(session)

        foundation_message = Message(
            message_id=str(uuid4()),
            session_id=session.session_id,
            role="system",
            content=f"Story foundation profile:\n{foundation_text}" if foundation_text else "Story foundation profile is not clearly.",
        )
        await self.store.add_message(foundation_message)

        ai_message = Message(
            message_id=str(uuid4()),
            session_id=session.session_id,
            role="ai",
            content=ai_text,
            choices=choices,
        )
        await self.memory.save_message(ai_message)

        session = await self.memory.refresh_summary(session)

        return StoryResponse(
            session_id=session.session_id,
            message=ai_text,
            choices=choices,
            foundation_text=session.foundation_text,
            session=session,
            gold=session.gold,
            inventory=session.inventory,
            party=session.party,
        )

    async def continue_story(self, request: TurnRequest, user_id: str, ) -> StoryResponse:
        session = await self.store.get_session(request.session_id)
        if session is None:
            raise ValueError("Session not found")
        if session.user_id != user_id:
            raise PermissionError("You do not own this session")
        user_message = Message(
            message_id=str(uuid4()),
            session_id=request.session_id,
            role="user",
            content=request.player_input,
        )
        await self.memory.save_message(user_message)

        recent = await self.memory.recent_messages(request.session_id)
        query = f"{request.player_input}\n{session.foundation_text}\n{session.story_summary}\n{session.character_summary}"
        relevant = await self.memory.relevant_memories(request.session_id, query)

        # ══════════════════════════════════════════════════════════════════
        # EVENT DIRECTOR  (deterministic 1-100 roll → 5 event branches)
        # ══════════════════════════════════════════════════════════════════
        # Clear previous turn's scratch-pad fields before rolling the new event.
        session.current_event     = None
        session.current_shop_data = None
        session.current_encounter = None

        roll = random.randint(1, 100)
        event_directive: str = ""
        combat_log = None   # only populated by NPC_ENCOUNTER combat path

        # ──────────────────────────────────────────────────────────────────
        # Branch 1 · PRIEST  (1-5, 5%)
        # Full-party heal + item grant scaled by priest_level.
        # ──────────────────────────────────────────────────────────────────
        if roll <= 5:
            session.current_event = "PRIEST"

            # Restore every party member to full HP
            for member in session.party:
                member.hp = member.max_hp

            # Grant healing potions equal to priest_level
            priest_potion = ITEM_BY_ID["potion_hp_full"]
            for _ in range(session.priest_level):
                self._add_to_inventory(session, priest_potion["name"], priest_potion["type"])

            # At priest_level >= 4 also grant Nước thánh
            if session.priest_level >= 4:
                holy_water = ITEM_BY_ID["holy_water"]
                self._add_to_inventory(session, holy_water["name"], holy_water["type"])

            # Build item list for the directive
            granted_items = f"{session.priest_level}x {priest_potion['name']}"
            if session.priest_level >= 4:
                granted_items += f" và {holy_water['name']}"

            event_directive = (
                "Kể cảnh nhóm gặp Tu sĩ ẩn danh, được ban phước hồi phục toàn bộ "
                f"sinh lực và nhận được vật phẩm thần thánh ({granted_items})."
            )

        # ──────────────────────────────────────────────────────────────────
        # Branch 2 · MERCHANT  (6-15, 10%)
        # Generate a shop grid of items + hireable NPCs.
        # ──────────────────────────────────────────────────────────────────
        elif roll <= 15:
            session.current_event = "MERCHANT"

            # Grid size scales with merchant_level
            grid_size = 4 if session.merchant_level == 1 else (
                5 if session.merchant_level == 2 else 6
            )

            # Sample items without replacement (clamp to catalogue size)
            shop_item_pool = random.sample(
                ITEM_DATA,
                k=min(grid_size, len(ITEM_DATA)),
            )

            # Generate hireable NPCs
            shop_npcs = [
                generate_npc(session.merchant_level)
                for _ in range(grid_size)
            ]

            session.current_shop_data = {
                "items": shop_item_pool,
                "npcs":  shop_npcs,
                "merchant_level": session.merchant_level,
            }

            event_directive = (
                "Kể cảnh nhóm bước vào một khu lều hoặc gặp một thương nhân lữ "
                "hành đang bày bán các món đồ ma pháp và có lính đánh thuê xung quanh."
            )

        # ──────────────────────────────────────────────────────────────────
        # Branch 3 · LOOT  (16-30, 15%)
        # Grant one random item from the catalogue; reset pity counter.
        # ──────────────────────────────────────────────────────────────────
        elif roll <= 30:
            session.current_event = "LOOT"
            session.item_pity_counter = 0   # reset pity on a loot drop

            loot_item = random.choice(ITEM_DATA)
            self._add_to_inventory(session, loot_item["name"], loot_item["type"])

            event_directive = (
                f"Kể cảnh nhóm tình cờ tìm thấy vật phẩm: {loot_item['name']} "
                "trong lúc khám phá."
            )

        # ──────────────────────────────────────────────────────────────────
        # Branch 4 · NPC_ENCOUNTER  (31-60, 30%)
        # Spawn one NPC whose allegiance is unknown. Run combat engine.
        # ──────────────────────────────────────────────────────────────────
        elif roll <= 60:
            session.current_event = "NPC_ENCOUNTER"
            session.item_pity_counter += 1

            npc = generate_npc(session.merchant_level)
            session.current_encounter = npc

            event_directive = (
                f"Kể cảnh nhóm chạm trán một nhân vật bí ẩn: "
                f"Tộc {npc['race']}, Nghề {npc['class_type']}. "
                f"Tả ngoại hình: {npc['visual_profile']}. "
                "Hiện tại chưa rõ địch hay bạn."
            )

            # Run the deterministic combat exchange against the NPC
            if session.party:
                active_hero = session.party[0]
                mock_enemy = {
                    "hp":          npc["hp"],
                    "atk":         npc["atk"],
                    "res_atk":     npc["res_atk"],
                    "atk_def":     npc["atk_def"],
                    "res_atk_def": npc["res_atk_def"],
                    "atk_spd":     npc["atk_spd"],
                }
                combat_log = calculate_exchange(active_hero, mock_enemy)

                # Apply hero HP damage
                active_hero.hp -= combat_log["hero_dmg_taken"]

                # Remove hero from party if dead
                if combat_log["hero_dead"]:
                    session.party.pop(0)

        # ──────────────────────────────────────────────────────────────────
        # Branch 5 · EXPLORATION  (61-100, 40%)
        # Pure narrative; no state changes.
        # ──────────────────────────────────────────────────────────────────
        else:
            session.current_event = "EXPLORATION"
            session.item_pity_counter += 1

            event_directive = (
                "Tiếp tục kể diễn biến khám phá thế giới dựa trên hành động của người chơi."
            )

        # ── Persist all mid-turn state changes to Firebase ────────────────
        session.updated_at = utc_now_iso()
        await self.store.update_session(session)

        # ══════════════════════════════════════════════════════════════════
        # GENERATE GAME STATE STRINGS FOR AI PROMPT
        # ══════════════════════════════════════════════════════════════════
        party_state_str     = self._generate_party_state_str(session)
        inventory_state_str = self._generate_inventory_state_str(session)

        prompt = build_turn_prompt(
            session,
            recent,
            relevant,
            request.player_input,
            target_words=request.target_words,
            event_directive=event_directive,
            combat_log=combat_log,
            party_state_str=party_state_str,
            inventory_state_str=inventory_state_str,
        )
        raw = await self.provider.generate_text(prompt)
        parsed = parse_story_output(raw)

        ai_text = parsed["story"]
        choices = parsed["choices"]
        state_updates = parsed.get("state_updates", {"gold_change": 0, "items_acquired": []})

        # ══════════════════════════════════════════════════════════════════
        # APPLY STATE UPDATES FROM AI (Gold & Items)
        # ══════════════════════════════════════════════════════════════════
        gold_change = state_updates.get("gold_change", 0)
        items_acquired = state_updates.get("items_acquired", [])
        
        # Update gold
        if gold_change != 0:
            session.gold += gold_change
        
        # Add acquired items to inventory (uses helper so stacking logic is consistent)
        for item_name in items_acquired:
            self._add_to_inventory(session, item_name, item_type="discovered")

        ai_message = Message(
            message_id=str(uuid4()),
            session_id=request.session_id,
            role="ai",
            content=ai_text,
            choices=choices,
        )
        await self.memory.save_message(ai_message)

        # Clear turn-state scratch-pad before final save
        session.current_event     = None
        session.current_shop_data = None
        session.current_encounter = None

        session.updated_at = utc_now_iso()
        await self.store.update_session(session)
        session = await self.memory.refresh_summary(session)

        return StoryResponse(
            session_id=session.session_id,
            message=ai_text,
            choices=choices,
            foundation_text=session.foundation_text,
            session=session,
            gold=session.gold,
            inventory=session.inventory,
            party=session.party,
        )

    async def get_session(self, session_id: str, user_id: str,):
        session = await self.store.get_session(session_id)
        if session is None:
            raise ValueError("Session not found")
        if session.user_id != user_id:
            raise PermissionError("You do not own this session")
        messages = await self.store.get_messages(session_id, limit=100)
        return session, messages
    async def debug_memory(self, session_id: str):
        session = await self.store.get_session(session_id)
        if session is None:
            raise ValueError("Session not found")

        messages = await self.store.get_messages(session_id, limit=30)
        memories = await self.vector_store.list_memories(session_id, limit=100)

        return {
            "session": session,
            "messages": messages,
            "memories": memories,
        }
    async def list_sessions(self, user_id: str):
        return await self.store.list_sessions(
                user_id=user_id,
                limit=30,
            )
    async def delete_session(self, session_id: str, user_id: str,):
        session = await self.store.get_session(session_id)

        if session is None:
            raise ValueError("Session not found")
        if session.user_id != user_id:
            raise PermissionError("You do not own this session")

        await self.vector_store.delete_memories(session_id)
        await self.store.delete_session(session_id)

        return {"success": True}
    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)
    async def start_novel_world(
        self,
        request: NovelStartRequest,
        user_id: str,
    ) -> NovelWorldResponse:
        session = SessionState(
            session_id=str(uuid4()),
            user_id=user_id,
            mode="novel",
            title=request.title or "Untitled Novel",
            world_seed=request.world_seed or "",
            target_words=request.target_words,
        )

        await self.store.create_session(session)

        prompt = build_novel_world_prompt(request.world_seed)
        raw = await self.provider.generate_text(prompt)
        data = self._parse_json(raw)

        world_draft = data.get("world_draft", "")
        questions = data.get("questions", [])

        session.world_summary = world_draft
        session.world_questions = questions
        session.novel_profile = {
            "world_draft": world_draft,
            "questions": questions,
        }
        session.updated_at = utc_now_iso()

        await self.store.update_session(session)

        return NovelWorldResponse(
            session_id=session.session_id,
            world_draft=world_draft,
            questions=questions,
            session=session,
        )
    async def create_novel_foundation(
        self,
        request: NovelFoundationRequest,
        user_id: str,
    ) -> StoryResponse:
        session = await self.store.get_session(request.session_id)

        if session is None:
            raise ValueError("Session not found")

        if session.user_id != user_id:
            raise PermissionError("You do not own this session")

        answers = [a.model_dump() for a in request.answers]

        session.world_answers = answers
        session.target_words = request.target_words

        prompt = build_novel_foundation_prompt(
            session=session,
            player_name=request.player_name,
            gender=request.gender,
            age=request.age,
            occupation=request.occupation,
            personality=request.personality,
            answers=answers,
            target_words=request.target_words,
        )

        raw = await self.provider.generate_text(prompt)
        data = self._parse_json(raw)

        foundation_text = data.get("foundation", "")
        novel_profile = data.get("novel_profile", {})
        ai_text = data.get("story", "")
        choices = data.get("choices", [])

        session.foundation_text = foundation_text
        session.novel_profile = novel_profile
        session.character_summary = json.dumps(
            novel_profile.get("protagonist", {}),
            ensure_ascii=False,
        )
        session.story_summary = "The novel has just begun."
        session.important_facts = [foundation_text]
        session.updated_at = utc_now_iso()

        await self.store.update_session(session)

        foundation_message = Message(
            message_id=str(uuid4()),
            session_id=session.session_id,
            role="system",
            content=f"Novel foundation profile:\n{foundation_text}",
        )
        await self.store.add_message(foundation_message)

        ai_message = Message(
            message_id=str(uuid4()),
            session_id=session.session_id,
            role="ai",
            content=ai_text,
            choices=choices,
        )
        await self.memory.save_message(ai_message)

        session = await self.memory.refresh_summary(session)

        return StoryResponse(
            session_id=session.session_id,
            message=ai_text,
            choices=choices,
            foundation_text=session.foundation_text,
            session=session,
            gold=session.gold,
            inventory=session.inventory,
            party=session.party,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _add_to_inventory(
        self,
        session: SessionState,
        item_name: str,
        item_type: str = "discovered",
        quantity: int = 1,
    ) -> None:
        """
        Add `quantity` of `item_name` to the session inventory.

        If an item with the same name already exists, its quantity is
        incremented.  Otherwise a new InventoryItem is appended.

        This is the single canonical path for all inventory mutations so
        that stacking logic is never duplicated across event branches.
        """
        existing = next(
            (i for i in session.inventory if i.name == item_name), None
        )
        if existing:
            existing.quantity += quantity
        else:
            session.inventory.append(
                InventoryItem(
                    item_id=str(uuid4()),
                    name=item_name,
                    quantity=quantity,
                    type=item_type,
                )
            )

    def _generate_party_state_str(self, session: SessionState) -> str:
        """
        Generates a human-readable party state string for the AI prompt.

        Args:
            session: The current SessionState
        
        Returns:
            A formatted string describing all party members and their stats
        """
        if not session.party:
            return "Party is empty (No active members)."
        
        party_lines = []
        for idx, member in enumerate(session.party, 1):
            status = "ACTIVE" if idx == 1 else "STANDBY"
            line = f"""
Member {idx} [{status}]: {member.name}
  - Class: {member.class_type}
  - HP: {member.hp}/{member.max_hp}
  - Physical Attack: {member.atk}
  - Magical Attack: {member.res_atk}
  - Physical Defense: {member.atk_def}%
  - Magical Defense: {member.res_atk_def}%
  - Speed (Initiative): {member.atk_spd}"""
            party_lines.append(line)
        
        return "\n".join(party_lines)
    
    def _generate_inventory_state_str(self, session: SessionState) -> str:
        """
        Generates a human-readable inventory state string for the AI prompt.
        
        Args:
            session: The current SessionState
        
        Returns:
            A formatted string describing all inventory items and gold
        """
        inventory_lines = []
        
        # Gold
        inventory_lines.append(f"Gold: {session.gold}")
        
        # Items
        if not session.inventory:
            inventory_lines.append("Items: None (Inventory is empty)")
        else:
            inventory_lines.append("Items:")
            for item in session.inventory:
                inventory_lines.append(f"  - {item.name} (Type: {item.type}, Quantity: {item.quantity})")
        
        return "\n".join(inventory_lines)