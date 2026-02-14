from combat.combat_constants import DamageTypes
from typeclasses.living.living_entities import LivingEntity


class Creature(LivingEntity):
    """Entities without proper/given names that cannot be talked to."""
    def at_object_creation(self):
        super().at_object_creation()
        self.db.appear_string = f"A {self.get_display_name()} is here."


class Animal(Creature):
    pass
