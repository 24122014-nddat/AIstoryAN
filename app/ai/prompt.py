from __future__ import annotations

from app.domain.models import Message, SessionState, MemoryChunk


def build_start_prompt(
    player_name: str,
    story_style: str | None,
    character_hint: str | None,
    world_hint: str | None,
    gender: str | None = None,
    personality: str | None = None,
) -> str:
    return f"""
You are the lead narrator for an AI Story Adventure.

IMPORTANT LANGUAGE RULE:
- All user-facing content inside the JSON values must be written in natural Vietnamese.
- Internal instructions are in English, but the actual story, foundation, and choices must be Vietnamese.

Goal:
- After the player rolls a character, create a clear long-term story foundation for future turns.
- The player is not merely reading the story; they are living inside the world.
- Do not create a fixed quest. Open a situation with multiple possible directions.

Return ONLY valid JSON.
Do not include markdown.
Do not wrap the response in ```json.
Do not explain anything outside the JSON.

Required format:
{{
  "foundation": "Vietnamese prose describing the world background + protagonist + origin + occupation/role/status + personality + important world details. This field is used as the long-term foundation profile for the session.",
  "story": "Vietnamese opening scene written directly in the present moment.",
  "choices": [
    "A short natural Vietnamese choice",
    "A short natural Vietnamese choice",
    "A short natural Vietnamese choice"
  ]
}}

Rules for foundation:
- Write 1 to 3 clear prose paragraphs in Vietnamese.
- Include the world setting, tone, and the main unusual rule/anomaly if any.
- Include the protagonist: name, gender if provided, personality, origin, occupation/status/current role.
- Include several important details that future turns can rely on.
- Do not write a nested JSON table inside the foundation field. It must be plain Vietnamese prose.

Rules for story:
- Start immediately with a concrete situation happening right now.
- Do not begin with phrases like "Bạn là..." or "Câu chuyện bắt đầu...".
- Write as if a camera is focusing directly on the current moment.
- Include a sense of danger, mystery, pressure, or something being wrong.
- The protagonist must be actively doing something, not simply standing still.

Rules for choices:
- Create exactly 3 short, natural Vietnamese choices that fit the situation.
- Do not number the choices.
- The player may still type any custom action outside the provided choices.

Player information:
Name: {player_name}
Gender: {gender or "Let the AI decide if needed"}
Personality: {personality or "Let the AI create"}
Desired style: {story_style or "Let the AI decide"}
Character/origin hint: {character_hint or "Let the AI create"}
World hint: {world_hint or "Let the AI create"}
""".strip()
def build_novel_world_prompt(world_seed: str | None) -> str:
    return f"""
You are a worldbuilding assistant for an interactive novel writing app.

The user may provide a world description, or may skip and let you create one.
Your job is NOT to write the story yet.
Your job is to create a strong world draft and ask questions that help shape the novel.

Return ONLY valid JSON.
Do not use markdown.
Do not wrap the result in ```json.
Do not explain anything outside the JSON.

Required JSON format:
{{
  "world_draft": "A rich but concise world description for an interactive novel. This should be useful as a story bible seed.",
  "questions": [
    {{
      "id": "q1",
      "question": "A question that helps define the protagonist, tone, conflict, stakes, or narrative direction.",
      "suggestions": [
        "Suggestion 1",
        "Suggestion 2",
        "Suggestion 3"
      ]
    }}
  ]
}}
IMPORTANT LANGUAGE RULE:
- All user-facing JSON values must be written in natural Vietnamese.
- This includes world_draft, questions, and suggestions.
- Internal instructions are English only.
Rules:
- If the user gives a world idea, expand it faithfully instead of replacing it.
- If the user skips or gives little detail, create an original world.
- The world should feel suitable for a novel, not a game stage.
- The questions should help define protagonist, age/role/occupation/personality, central conflict, tone, taboo/rule of the world, and opening direction.
- Create 4 to 6 questions.
- Each question should include 3 suggestions, but the player may answer freely.
- Avoid generic questions. Make the questions specific to the generated world.
- Do not start the story yet.

User world idea:
{world_seed or "User skipped. Create an original world."}
""".strip()


def build_novel_foundation_prompt(
    session: SessionState,
    player_name: str,
    gender: str | None,
    age: str | None,
    occupation: str | None,
    personality: str | None,
    answers: list[dict],
    target_words: int,
) -> str:
    return f"""
You are the lead novelist for an interactive AI novel.
IMPORTANT LANGUAGE RULE:
- All user-facing JSON values must be written in natural Vietnamese.
- This includes foundation, novel_profile values, story, and choices.
- Internal instructions are English only.
You will receive:
- a world draft,
- the player's answers to worldbuilding questions,
- protagonist basics.

Your task:
1. Create a novel profile / story bible for future writing.
2. Write the opening prose of the novel.
3. Create longer narrative choices suitable for a novel.

Return ONLY valid JSON.
Do not use markdown.
Do not wrap the result in ```json.
Do not explain anything outside the JSON.

Required JSON format:
{{
  "foundation": "A complete Vietnamese prose-style novel bible summary. Include world setting, protagonist profile, age, gender, occupation, personality, tone, central conflict, rules of the world, important details, and opening situation.",
  "novel_profile": {{
    "world_setting": "...",
    "genre": "...",
    "tone": "...",
    "protagonist": {{
      "name": "...",
      "age": "...",
      "gender": "...",
      "occupation": "...",
      "personality": "..."
    }},
    "main_conflict": "...",
    "world_rules": ["..."],
    "important_notes": ["..."]
  }},
  "story": "The Vietnamese opening prose of the novel.",
    "choices": [
    "A longer Vietnamese narrative direction choice.",
    "Another longer Vietnamese narrative direction choice.",
    "Another longer Vietnamese narrative direction choice."
    ]
}}

Important:
- novel_profile is only a reference document for the AI to read later.
- Do NOT treat novel_profile as game stats.
- Do NOT include HP, inventory, levels, combat stats, or RPG mechanics.
- Write like a novel, not like a game log.
- The player is co-authoring the protagonist's path.
- The protagonist should be vivid and usable for long-form fiction.
- The opening should begin with an immediate scene, not an encyclopedia entry.
- Choices should be longer than adventure-game choices and should describe narrative directions.
- Choices must not be numbered.
- Target opening length: about {target_words} words.
- Do not mention AI, prompt, system, JSON, or model.

World draft:
{session.world_summary or session.world_seed or "No world draft available. Create a coherent original foundation."}

Player answers:
{answers}

Protagonist basics:
Name: {player_name}
Gender: {gender or "AI may decide"}
Age: {age or "AI may decide"}
Occupation: {occupation or "AI may decide"}
Personality: {personality or "AI may decide"}
""".strip()


def build_turn_prompt(
    session: SessionState,
    recent_messages: list[Message],
    relevant_memories: list[MemoryChunk],
    player_input: str,
    target_words: int = 600,
    event_directive: str = "Tiếp tục kể diễn biến khám phá thế giới dựa trên hành động của người chơi.",
    combat_log: dict = None,
    party_state_str: str = "No party state available.",
    inventory_state_str: str = "Empty inventory.",
) -> str:
    recent_text = "\n".join(
        [f"{m.role.upper()}: {m.content}" for m in recent_messages]
    ) or "None."

    memory_text = "\n".join(
        [f"- {m.text}" for m in relevant_memories]
    ) or "None."

    facts = "\n".join(
        [f"- {x}" for x in session.important_facts]
    ) or "None."

    mode = getattr(session, "mode", "adventure")
    novel_profile = getattr(session, "novel_profile", {}) or {}
    is_novel = mode == "novel"

    # ═══════════════════════════════════════════════════════════════════════════
    # COMBAT LOG INSTRUCTION (Deterministic Combat Rule Binding)
    # ═══════════════════════════════════════════════════════════════════════════
    combat_instruction = ""
    if combat_log:
        combat_instruction = f"""
╔═══════════════════════════════════════════════════════════════════════╗
║                  CRITICAL COMBAT RULE (Binding AI)                   ║
╚═══════════════════════════════════════════════════════════════════════╝

A combat exchange just occurred based on backend deterministic math.
You MUST narrate this exact mechanical outcome in Vietnamese.
DO NOT invent different damage results or resurrect dead characters.

COMBAT MECHANICS (Backend-Calculated):
- First to Attack (Initiative): {combat_log["first_attacker"]}
- Hero Damage Type: {combat_log["hero_dmg_type"]} (describe weapon strikes for 'physical', spells/magic for 'magical')
- Hero Dealt Damage: {combat_log["hero_dmg_dealt"]} damage
- Hero Took Damage: {combat_log["hero_dmg_taken"]} damage
- Enemy Dead?: {combat_log["enemy_dead"]} (If yes, emphasize target died instantly without counter-attack)
- Hero Dead?: {combat_log["hero_dead"]}

YOUR NARRATIVE CONSTRAINTS:
1. Describe the {combat_log["hero_dmg_type"]} attack method in vivid detail (weapon/spell).
2. State that the hero dealt exactly {combat_log["hero_dmg_dealt"]} damage.
3. If enemy is dead ({combat_log["enemy_dead"]}), describe the instant death without counter-attack.
4. If enemy survived, describe the counter-attack and hero taking exactly {combat_log["hero_dmg_taken"]} damage.
5. If hero is dead ({combat_log["hero_dead"]}), narrate the hero's defeat and potential party consequences.
6. Make this dramatic and immersive, but always respect the math above.

DO NOT override these backend calculations with invented story outcomes.
╚═══════════════════════════════════════════════════════════════════════╝
"""

    if is_novel:
        mode_instruction = f"""
You are writing an interactive literary novel.

Return ONLY valid JSON.
Do not include markdown.
Do not wrap the response in ```json.
Do not explain anything outside the JSON.

Required format:
{{
  "story": "The next prose section of the novel.",
  "choices": [
    "A longer narrative direction choice.",
    "Another longer narrative direction choice.",
    "Another longer narrative direction choice."
  ],
  "state_updates": {{
    "gold_change": 0,
    "items_acquired": []
  }}
}}

CRITICAL: All three keys ("story", "choices", "state_updates") MUST be present in your JSON.

Novel writing rules:
- Write literary prose, not a game log.
- Continue directly from the player's chosen direction or custom input.
- Respect the novel profile, story bible, previous events, memories, and summaries.
- Maintain continuity with the established world, tone, characters, and rules.
- Do not contradict established facts unless there is a believable in-world reason.
- Do not mention AI, prompts, memory systems, JSON, or technical concepts.
- Avoid excessive summarization. Write scenes as if they are unfolding in real time.
- Use atmosphere, sensory detail, emotion, tension, subtext, and character interiority.
- Keep continuity with the protagonist's identity, age, occupation, personality, and emotional state.
- Choices should feel like meaningful narrative directions, not simple gameplay commands.
- The player is co-authoring the protagonist's journey.
- The player may ignore choices and freely write custom actions.
- Target length: about {target_words} Vietnamese words.
""".strip()

    else:
        mode_instruction = f"""
You are the lead narrator for an AI Story Adventure RPG system.
The backend Python engine manages all combat math, RNG events, and state changes.
You are the Dungeon Master. Your job is to narrate the story and optionally communicate game state changes.

Return ONLY valid JSON.
Do not include markdown.
Do not wrap the response in ```json.
Do not explain anything outside the JSON.

Required format:
{{
  "story": "The next scene of the story.",
  "choices": [
    "A natural Vietnamese choice.",
    "A natural Vietnamese choice.",
    "A natural Vietnamese choice."
  ],
  "state_updates": {{
    "gold_change": 0,
    "items_acquired": []
  }}
}}

CRITICAL: All three keys ("story", "choices", "state_updates") MUST be present in your JSON.

State Updates Rules:
- gold_change: An integer. Positive for gold gained, negative for gold spent. Default 0.
  Example: The hero finds 50 gold coins → "gold_change": 50
  Example: The hero buys something for 30 gold → "gold_change": -30
- items_acquired: An array of item names (strings) discovered or acquired in this turn. Default [].
  Example: The hero finds a sword and a potion → "items_acquired": ["Rusty Sword", "Healing Potion"]
  If no items found, use empty array: "items_acquired": []

Adventure writing rules:
- Continue directly from the player's latest action or dialogue.
- Respect established memories, events, worldbuilding, and character identity.
- Maintain continuity and logical causality.
- The world may evolve unpredictably, but it must remain believable.
- Do not mention AI, prompts, systems, JSON, or memory mechanisms.
- Write scenes as if they are happening in real time.
- Avoid excessive exposition or repetition.
- Focus on atmosphere, movement, tension, emotion, and direct scene progression.
- The protagonist must actively participate in the scene.
- Choices should represent actions or directions immediately available in the current moment.
- Target length: about {target_words} Vietnamese words.
""".strip()

    return f"""
IMPORTANT LANGUAGE RULE:
All narration, prose, dialogue, atmosphere, descriptions, thoughts, and choices visible to the player must be written entirely in natural literary Vietnamese.

{mode_instruction}

{combat_instruction}

═══════════════════════════════════════════════════════════════════════════════
╔══════════════════════════ RPG GAME STATE ══════════════════════════════════╗
═══════════════════════════════════════════════════════════════════════════════

PARTY STATUS:
{party_state_str}

INVENTORY:
{inventory_state_str}

═══════════════════════════════════════════════════════════════════════════════
╔══════════════════ CRITICAL SYSTEM DIRECTIVE FOR THIS TURN ═════════════════╗
═══════════════════════════════════════════════════════════════════════════════

{event_directive}

You MUST weave this exact event naturally into the Vietnamese story narrative.
Do not invent different items or events than what is stated here.
Do not explicitly announce the directive text to the player — make it feel organic.

═══════════════════════════════════════════════════════════════════════════════

=== SESSION MODE ===
{mode}

=== NOVEL PROFILE ===
{novel_profile if is_novel else "Not a novel session."}

=== STORY FOUNDATION ===
{session.foundation_text}

=== WORLD SUMMARY ===
{session.world_summary}

=== CHARACTER SUMMARY ===
{session.character_summary}

=== STORY SUMMARY ===
{session.story_summary}

=== IMPORTANT FACTS ===
{facts}

=== RELEVANT MEMORIES ===
{memory_text}

=== RECENT MESSAGES ===
{recent_text}

=== PLAYER INPUT ===
{player_input}
""".strip()


def build_summary_prompt(
    session: SessionState,
    messages: list[Message],
) -> str:
    text = "\n".join(
        [f"{m.role}: {m.content}" for m in messages]
    )

    mode = getattr(session, "mode", "adventure")
    novel_profile = getattr(session, "novel_profile", {}) or {}

    if mode == "novel":
        return f"""
You are maintaining long-term memory for an interactive AI novel.

IMPORTANT LANGUAGE RULE:
- All summary content must be written in concise Vietnamese.
- Internal instructions are English only.

Return EXACTLY these 4 sections.
Do not return JSON.
Do not add markdown.
Do not add explanations.

Required structure:

WORLD_SUMMARY:
A concise Vietnamese summary of:
- world setting
- rules
- tone
- major conflicts
- important locations
- supernatural or political systems if relevant

CHARACTER_SUMMARY:
A concise Vietnamese summary of:
- protagonist identity
- personality
- role/occupation
- emotional state
- relationships
- character development

STORY_SUMMARY:
A concise Vietnamese summary of:
- major story events
- discoveries
- conflicts
- decisions
- consequences

IMPORTANT_FACTS:
3 to 8 important Vietnamese facts separated ONLY by semicolons.

Novel profile / story bible:
{novel_profile}

Story foundation:
{session.foundation_text}

Previous memory:
WORLD_SUMMARY: {session.world_summary}
CHARACTER_SUMMARY: {session.character_summary}
STORY_SUMMARY: {session.story_summary}
IMPORTANT_FACTS: {'; '.join(session.important_facts)}

New messages:
{text}
""".strip()

    return f"""
You are maintaining long-term memory for an AI Story Adventure.

IMPORTANT LANGUAGE RULE:
- All summary content must be written in concise Vietnamese.
- Internal instructions are English only.

Return EXACTLY these 4 sections.
Do not return JSON.
Do not add markdown.
Do not add explanations.

Required structure:

WORLD_SUMMARY:
A concise Vietnamese summary of:
- world setting
- tone
- dangers
- important rules
- important factions or locations

CHARACTER_SUMMARY:
A concise Vietnamese summary of:
- protagonist identity
- role
- personality
- current motivations
- emotional state

STORY_SUMMARY:
A concise Vietnamese summary of:
- important events
- discoveries
- conflicts
- consequences
- current situation

IMPORTANT_FACTS:
3 to 8 important Vietnamese facts separated ONLY by semicolons.

Story foundation:
{session.foundation_text}

Previous memory:
WORLD_SUMMARY: {session.world_summary}
CHARACTER_SUMMARY: {session.character_summary}
STORY_SUMMARY: {session.story_summary}
IMPORTANT_FACTS: {'; '.join(session.important_facts)}

New messages:
{text}
""".strip()


def build_memory_extract_prompt(message_text: str) -> str:
    return f"""
You are a memory extraction system for an AI Story Adventure / Interactive Novel.

IMPORTANT LANGUAGE RULE:
- All extracted memories must be written in concise Vietnamese.
- Internal instructions are English only.

Your task:
- Read the passage below.
- Extract 1 to 6 important long-term memories.
- Each memory must be a short, clear Vietnamese sentence.
- Only extract meaningful information useful for future continuity.

Focus on:
- important events
- discoveries
- items or artifacts
- locations
- NPCs
- promises
- secrets
- goals
- relationships
- emotional changes
- major decisions
- world rules
- political or supernatural developments

Rules:
- Do not explain anything.
- Do not return JSON.
- One memory per line.
- Keep memories concise and information-dense.
- Ignore unimportant details or filler narration.
- If nothing important exists, return ONLY:
NONE

Text to analyze:
{message_text}
""".strip()
