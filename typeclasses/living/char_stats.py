from enum import Enum


class CharAttrib(Enum):
    STRENGTH = 1
    CONSTITUTION = 2
    DEXTERITY = 3
    PERCEPTION = 4
    INTELLIGENCE = 5
    WISDOM = 6
    SPIRIT = 7

    def get_display_name(self):
        return self.name.lower().capitalize()

    def get_short_name(self):
        return self.name[:3]