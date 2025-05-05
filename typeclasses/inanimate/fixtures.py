from typeclasses.base.objects import Object


class Fixture(Object):
    """
    Key immovable room features that appear in their own line in the room description.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.locks.add("get:false()")


class Fireplace(Fixture):
    """Having a fireplace in the room triples regeneration rates."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "Heat pours out of the crackling fireplace."


class Fountain(Fixture):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "Water trickles down the fountain."


class Well(Fixture):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.empty = False
        self.db.desc = "There is a well here."
