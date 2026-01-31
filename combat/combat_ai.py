import random

from evennia.utils import delay

from combat.abilities.abilities import Ability
from combat.abilities.all_abilities import HEALING_ABILITIES
from combat.combat_constants import DIRECTION_NAMES_OPPOSITES
from combat.combat_grid import DIRECTIONS
from combat.combat_handler import COMBAT
from typeclasses.inanimate.items.usables import Usable
from typeclasses.scripts.scripts import Script

# TODO: enemy turns time out after server restart

class CombatAI(Script):
    """Dictates how an entity decides to take actions in combat."""

    def at_script_creation(self):
        super().at_script_creation()
        if not self.key:
            self.key = self.__class__.__name__

    def take_turn(self):
        """While the entity has AP remaining, choose and perform an action."""
        if not self.obj.is_in_combat():
            return
        if not self.obj.is_turn():
            return
        if not self.check_ap():
            return
        action, target = self.choose_action()
        # Less delay between steps than other actions
        time = 1 if action in ("n", "s", "e", "w") else 2
        delay(time, self.perform_action, action=action, target=target)

    def check_ap(self):
        entity = self.obj
        ap_left = entity.db.combat_ap
        if ap_left > 0:
            return True
        else:
            return False

    def choose_action(self):
        """By default, attempts to heal if below 25% HP, attempts to use offensive abilities, then defaults to
        attack."""
        # Must run if under Fear effect
        fear_script = self.obj.effect_active("Afraid")
        if fear_script:
            caster = fear_script.db.caster
            grid = self.obj.db.combat_turnhandler.db.grid
            direction_moved = grid.move_toward(self.obj, caster, away=True)
            if direction_moved:
                return direction_moved, caster

        # Choices in order of priority
        for choice in [self.try_heal_below(25), self.try_offensive_abilities(), self.try_attack()]:
            if choice:
                break

        if not choice:
            choice = "pass", None
        return choice

    def choose_target(self, action):
        """By default, chooses a random fighter on the enemy side for offensive moves, or self for non-offensive."""
        entity = self.obj
        weapon = entity.get_weapon()

        # TODO: May need a marker for whether items are offensive
        # Attack or offensive ability
        if action == weapon or (isinstance(action, Ability) and action.db.offensive):
            in_range_targets = []
            all_enemy_targets = {}

            for fighter in self.obj.location.scripts.get("Combat Turn Handler")[0].db.fighters:
                if (fighter.db.hostile_to_players != self.obj.db.hostile_to_players  # If not an ally
                        and fighter.db.hp > 0):  # And not already downed

                    distance = entity.db.combat_turnhandler.db.grid.distance(entity, fighter)
                    rng = COMBAT.action_range(action)
                    if distance <= rng:
                        in_range_targets.append(fighter)
                    else:
                        all_enemy_targets[fighter] = distance

            # Fighters in range
            if len(in_range_targets) > 0:
                target = random.choice(in_range_targets)
                return target

            # Fighters out of range
            all_enemy_targets = sorted(all_enemy_targets.items(), key=lambda item: item[1])
            return all_enemy_targets[0][0]

        else:
            return entity

    def perform_action(self, action, target=None):
        entity = self.obj

        if action == entity.get_weapon():
            self.obj.attack(target)

        elif isinstance(action, Ability):
            action.cast(caster=entity, target=target)

        elif isinstance(action, Usable):
            COMBAT.use_item(user=entity, item=action, target=target)

        elif action in DIRECTIONS:
            # Already moved if possible
            dirname = DIRECTION_NAMES_OPPOSITES[action][0]
            entity.location.msg_contents(f"{entity.get_display_name(capital=True)} moves {dirname}.")

        elif action == "pass":
            entity.location.msg_contents(f"{entity.get_display_name(capital=True)} passes the turn.")
            entity.db.combat_lastaction = action
            entity.db.combat_turnhandler.next_turn()
            return  # Stop without calling take_turn

        entity.db.combat_lastaction = action
        if entity.is_turn():
            self.take_turn()

    def try_heal_below(self, percent_health: int):
        """If entity's HP is below the percent given, looks for a healing ability or item to use."""

        def use_heal_ability(entity):
            for ability in entity.db.abilities:
                if type(ability) in HEALING_ABILITIES.values():
                    if ability.check(caster=entity, target=entity):
                        return ability

        def use_heal_item(entity):
            for content in entity.contents:
                if content.attributes.has("item_func") and content.db.item_func == "heal":
                    return content

        entity = self.obj
        decimal = percent_health / 100
        minimum = decimal * entity.get_max("hp")

        if entity.db.hp < minimum:
            for possible_action in [use_heal_ability, use_heal_item]:
                action = possible_action(entity)
                if action:
                    return action, entity

        return False

    def try_offensive_abilities(self):
        """Looks for offensive abilities available to the entity, and casts them if possible."""
        entity = self.obj
        if entity.effect_active("Ceasefire"):
            return

        offensive_abilities = [ability for ability in entity.db.abilities if ability.db.offensive]
        while len(offensive_abilities) > 0:
            ability = random.choice(offensive_abilities)
            target = self.choose_target(ability)
            if target:  # If a good target is found for this ability
                if ability.check(caster=entity, target=self.choose_target(ability)):
                    return ability, target
                else:
                    offensive_abilities.remove(ability)
            else:
                offensive_abilities.remove(ability)

        return

    def try_attack(self):
        """Attempts to attack, or move closer if out of range."""
        entity = self.obj

        # Can't attack during Ceasefire
        if entity.effect_active("Ceasefire"):
            return

        # Tile effects that prevent attacking
        tile_effects = [eff.db.effect_key for eff in
                        entity.db.combat_turnhandler.db.grid.effects_at(entity.db.combat_x, entity.db.combat_y)]
        # Can't attack in a swarm
        if "Swarm" in tile_effects:
            return

        weapon = entity.get_weapon()
        target = self.choose_target(weapon)

        # In range? Move toward if not
        if entity.db.combat_ap < 1:
            return
        grid = entity.db.combat_turnhandler.db.grid
        if grid.distance(entity, target) > COMBAT.action_range(weapon):
            # Can't move when stuck
            if self.obj.effect_active("Stuck"):
                return
            direction_moved = grid.move_toward(entity, target)
            if direction_moved:
                return direction_moved, target

        # Enough AP?
        if target and entity.db.combat_ap >= entity.ap_to_attack():
            return weapon, target
