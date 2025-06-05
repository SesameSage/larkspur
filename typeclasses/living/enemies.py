from server import appearance
from typeclasses.living.characters import NPC
from typeclasses.living.living_entities import LivingEntity


class Enemy(LivingEntity):
    """An entity hostile to players, appearing red in text."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.hostile_to_players = True
        # TODO: Hostility to specific characters

    def color(self):
        return appearance.enemy


class EnemyCharacter(Enemy, NPC):
    def at_object_creation(self):
        super().at_object_creation()
        # Clear friendly default talk responses set on NPCs
        self.db.talk_responses = {}
