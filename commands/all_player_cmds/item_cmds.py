from evennia.commands.command import Command
from evennia.commands.cmdset import CmdSet

from server import appearance
from typeclasses.inanimate.items.items import Item


class CmdIdentify(Command):
    """
    view item details

    Usage:
      id <item>

    View stats and details on an item.
    """
    key = "identify"
    aliases = "id"
    help_category = "items"

    def func(self):
        if self.args:
            target = self.caller.search(self.args)
            if not target:
                self.caller.msg(f"Can't find '{self.args}' here")
                return
            if not isinstance(target, Item):
                self.caller.msg(f"{target.name.capitalize()} is not an item!")
                return
        else:
            self.caller.msg(f"Usage: {appearance.cmd}id <item>")
            return
        self.caller.msg(target.identify())


class CmdShop(Command):
    """
    view purchaseables

    List items available for purchase here.
    """
    key = "shop"
    help_category = "items"

    def func(self):
        # Look for a vendor here
        vendor = None
        for object in self.caller.location.contents:
            if object.attributes.has("stock"):
                vendor = object
        if not vendor:
            self.caller.msg("No one to buy from here!")
            return
        # Show their wares to the caller
        vendor.display_stock(self.caller)


class CmdBuy(Command):
    """
    buy an item from shop

    Usage:
      buy <item>

    Exchange your gold for an item shown in the shop.
    """
    key = "buy"
    help_category = "items"

    def func(self):
        vendor = None
        for object in self.caller.location.contents:
            if object.attributes.has("stock"):
                vendor = object
        if not vendor:
            self.caller.msg("No one to buy from here!")
            return
        if not self.args:
            self.caller.msg("Buy what?")
            return
        vendor.sell_item(player=self.caller, input=self.args)


class ItemCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdIdentify)
        self.add(CmdShop)
        self.add(CmdBuy)
