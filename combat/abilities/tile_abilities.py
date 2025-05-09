"""Abilities cast with a coordinate on the battlefield targeted instead of an object."""

from combat.abilities.abilities import TileAbility
from combat.combat_constants import SECS_PER_TURN


class Swarm(TileAbility):
    desc = ("Call insects to swarm on the battlefield, preventing anyone caught in the swarm from attacking or using "
            "abilities.")

    def at_object_creation(self):
        super().at_object_creation()
        self.db.offensive = True
        self.db.range = 5

        self.db.requires = [("intelligence", 3)]
        self.db.ap_cost = 2
        self.db.cost = [("mana", 6)]
        self.db.cooldown = 5 * SECS_PER_TURN
