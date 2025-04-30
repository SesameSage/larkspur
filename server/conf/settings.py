r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""
from evennia.settings_default import *

# Use the defaults from Evennia unless explicitly overridden

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "Larkspur"

AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False
AUTO_PUPPET_ON_LOGIN = False
MAX_NR_CHARACTERS = 10

BASE_ACCOUNT_TYPECLASS = "typeclasses.ooc.accounts.Account"
BASE_OBJECT_TYPECLASS = "typeclasses.base.objects.Object"
BASE_CHARACTER_TYPECLASS = "typeclasses.living.players.PlayerCharacter"
BASE_ROOM_TYPECLASS = "world.locations.rooms.Room"
BASE_EXIT_TYPECLASS = "world.locations.exits.Exit"
BASE_SCRIPT_TYPECLASS = "typeclasses.scripts.scripts.Script"
BASE_CHANNEL_TYPECLASS = "typeclasses.ooc.channels.Channel"

PROTOTYPE_MODULES = ["world.prototypes.prototypes", "world.prototypes.entity_protos", "world.prototypes.item_protos",
                     "world.prototypes.equipment.weapon_protos", "world.prototypes.consumable_protos",
                     "world.prototypes.equipment.armor_protos", "world.prototypes.equipment.apparel_protos",
                     "world.prototypes.equipment.equipment_protos", "world.prototypes.spellcomp_protos"]
FILE_HELP_ENTRY_MODULES = ["world.help_entries", "combat.help_combat", "typclasses.living.help_characters",
                           "typeclasses.inanimate.items.help_items", "typeclasses.ooc.help_ooc",
                           "combat.help_abilities",]

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
