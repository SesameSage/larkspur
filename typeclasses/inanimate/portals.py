from typeclasses.inanimate.fixtures import Fixture

PORTAL_KEY_TO_ROOM = {
    "Napasso": "#212"
}


class Portal(Fixture):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "The world appears to bend and stretch around a rift of blinding light."
        self.aliases.add("rift")


