"""
Deterministic Combat Engine for text-based RPG.
Handles all combat math, damage calculation, initiative, and turn resolution.
"""

from app.domain.models import PartyMember


def calculate_exchange(hero: PartyMember, enemy: dict) -> dict:
    """
    Resolves a single combat exchange between hero and enemy.
    
    Args:
        hero: PartyMember object with stats (hp, atk, res_atk, atk_def, res_atk_def, atk_spd)
        enemy: Dictionary with enemy stats
               Expected keys: hp, atk, res_atk, atk_def, res_atk_def, atk_spd
    
    Returns:
        combat_log: Dictionary containing:
            - first_attacker: "hero" or "enemy"
            - hero_dmg_type: "physical" or "magical"
            - hero_dmg_dealt: int (damage hero deals)
            - hero_dmg_taken: int (damage hero receives)
            - enemy_dead: bool (is enemy dead after exchange)
            - hero_dead: bool (is hero dead after exchange)
    """
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 1: CALCULATE HERO DAMAGE
    # ═══════════════════════════════════════════════════════════════
    # Hero Physical Damage = base atk reduced by enemy's physical defense
    hero_physical_dmg = max(
        1,
        int(round(hero.atk * (1 - enemy.get('atk_def', 0) / 100.0)))
    )
    
    # Hero Magical Damage = base res_atk reduced by enemy's magical defense
    hero_magical_dmg = max(
        1,
        int(round(hero.res_atk * (1 - enemy.get('res_atk_def', 0) / 100.0)))
    )
    
    # Choose higher damage and determine type
    if hero_physical_dmg >= hero_magical_dmg:
        hero_final_damage = hero_physical_dmg
        hero_dmg_type = "physical"
    else:
        hero_final_damage = hero_magical_dmg
        hero_dmg_type = "magical"
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 2: CALCULATE ENEMY DAMAGE
    # ═══════════════════════════════════════════════════════════════
    # Enemy Physical Damage = base atk reduced by hero's physical defense
    enemy_physical_dmg = max(
        1,
        int(round(enemy.get('atk', 0) * (1 - hero.atk_def / 100.0)))
    )
    
    # Enemy Magical Damage = base res_atk reduced by hero's magical defense
    enemy_magical_dmg = max(
        1,
        int(round(enemy.get('res_atk', 0) * (1 - hero.res_atk_def / 100.0)))
    )
    
    # Choose higher damage
    enemy_final_damage = max(enemy_physical_dmg, enemy_magical_dmg)
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 3: DETERMINE INITIATIVE (TURN ORDER)
    # ═══════════════════════════════════════════════════════════════
    hero_spd = hero.atk_spd
    enemy_spd = enemy.get('atk_spd', 0)
    
    if hero_spd > enemy_spd:
        first_attacker = "hero"
    elif enemy_spd > hero_spd:
        first_attacker = "enemy"
    else:  # Tie: hero goes first
        first_attacker = "hero"
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 4: RESOLVE COMBAT EXCHANGE
    # ═══════════════════════════════════════════════════════════════
    hero_dmg_taken = 0
    enemy_dead = False
    hero_dead = False
    
    if first_attacker == "hero":
        # Hero attacks first
        enemy_hp_after_hero_attack = enemy.get('hp', 100) - hero_final_damage
        
        if enemy_hp_after_hero_attack <= 0:
            # Enemy is dead, no counter-attack
            enemy_dead = True
            hero_dmg_taken = 0
        else:
            # Enemy survives and counter-attacks
            hero_dmg_taken = enemy_final_damage
            if hero.hp - hero_dmg_taken <= 0:
                hero_dead = True
    
    else:  # Enemy attacks first
        # Enemy attacks first
        hero_hp_after_enemy_attack = hero.hp - enemy_final_damage
        
        if hero_hp_after_enemy_attack <= 0:
            # Hero is dead, no counter-attack
            hero_dead = True
            hero_dmg_taken = enemy_final_damage
        else:
            # Hero survives and counter-attacks
            hero_dmg_taken = enemy_final_damage
            enemy_hp_after_hero_attack = enemy.get('hp', 100) - hero_final_damage
            if enemy_hp_after_hero_attack <= 0:
                enemy_dead = True
    
    # ═══════════════════════════════════════════════════════════════
    # RETURN COMBAT LOG
    # ═══════════════════════════════════════════════════════════════
    combat_log = {
        "first_attacker": first_attacker,
        "hero_dmg_type": hero_dmg_type,
        "hero_dmg_dealt": hero_final_damage,
        "hero_dmg_taken": hero_dmg_taken,
        "enemy_dead": enemy_dead,
        "hero_dead": hero_dead,
    }
    
    return combat_log
