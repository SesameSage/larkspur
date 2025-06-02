from evennia.commands.cmdset import CmdSet
from evennia.contrib.grid.simpledoor import SimpleDoorCmdSet

from commands.all_player_cmds.combat_cmds import BattleCmdSet
from commands.all_player_cmds.communication_cmds import CommsCmdSet
from commands.all_player_cmds.info_cmds import InfoCmdSet
from commands.all_player_cmds.interaction_cmds import InteractionCmdSet
from commands.all_player_cmds.item_cmds import ItemCmdSet
from commands.all_player_cmds.refiled_cmds import RefiledCmdSet
from commands.all_player_cmds.stats_cmds import StatsCmdSet
from commands.perm_cmds.building_cmds import BuildingCmdSet
from commands.perm_cmds.game_data_cmds import GameDataCmdSet
from commands.perm_cmds.location_data_cmds import LocationCmdSet
from commands.perm_cmds.object_data_cmds import ObjectDataCmdSet
from commands.perm_cmds.questbuild_cmds import QuestBuildCmdSet
from typeclasses.inanimate.items.containers import ContainerCmdSet
from typeclasses.inanimate.items.equipment.equipment import EquipmentCharacterCmdSet
from typeclasses.living.talking_npc import TalkingCmdSet


class PlayerCmdSet(CmdSet):
    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        # General
        self.add(StatsCmdSet)
        self.add(InfoCmdSet)
        self.add(CommsCmdSet)
        self.add(BattleCmdSet)
        self.add(ItemCmdSet)

        # Specific objects
        self.add(InteractionCmdSet)
        self.add(TalkingCmdSet)
        self.add(SimpleDoorCmdSet)
        self.add(EquipmentCharacterCmdSet)
        self.add(ContainerCmdSet)

        # Refiled under different help categories
        self.add(RefiledCmdSet)

        # Builders only
        self.add(GameDataCmdSet)
        self.add(BuildingCmdSet)
        self.add(LocationCmdSet)
        self.add(QuestBuildCmdSet)
        self.add(ObjectDataCmdSet)


