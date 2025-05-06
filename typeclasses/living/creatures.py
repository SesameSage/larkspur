from combat.effects import DamageTypes
from typeclasses.living.enemies import Enemy
from typeclasses.living.living_entities import LivingEntity


class Creature(LivingEntity):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.appear_string = f"A {self.get_display_name()} is here."


class Beast(Creature):
    def at_object_creation(self):
        super().at_object_creation()
        # Natural armor and agility
        self.db.char_defense = {None: 10}
        self.db.char_evasion = 20
        self.db.attribs["strength"] = 5
        self.db.attribs["dexterity"] = 5
        # Unarmed attack is bite
        self.db.unarmed_attack = "bite"
        self.db.unarmed_damage = {DamageTypes.CRUSHING: (2, 5)}


class EnemyBeast(Enemy, Beast):
    pass


class Animal(Beast):
    pass
