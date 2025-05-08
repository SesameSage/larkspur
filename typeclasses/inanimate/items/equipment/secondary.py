from typeclasses.inanimate.items.equipment.equipment import Equipment


class HeldItem(Equipment):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.equipment_slot = "secondary"

