from evennia import Command


class CmdMoreInfo(Command):
    """
        toggle seeing real-time combat calculations

        Usage:
          moreinfo

        This command changes the moreinfo preference for this character.
        Setting moreinfo to True displays an array of faded messages
        on the status of calculations in combat.
        """
    key = "moreinfo"
    help_category = "appearance"

    def func(self):
        self.caller.attributes.get("prefs", category="ooc")["more_info"] = \
            not self.caller.attributes.get("prefs", category="ooc")["more_info"]
        self.caller.print_ambient(
            f"MoreInfo set to {self.caller.attributes.get("prefs", category="ooc")["more_info"]}.")


class CmdHere(Command):
    """
        see info on your location

        Usage:
          here

        The "here" command shows your current room's area, locality,
        zone, and region.
        """
    key = "here"
    help_category = "navigation"

    def func(self):
        room = self.caller.location
        area = room.db.area.key if room.db.area else "None"
        locality = room.locality().key if room.locality() else "None"
        zone = room.zone().key if room.zone() else "None"
        region = room.region().key if room.region() else "None"

        self.caller.msg(f"|wRoom:|n {room.get_display_name()}\n"
                        f"|wArea:|n {area}\n"
                        f"|wLocality:|n {locality}\n"
                        f"|wZone:|n {zone}\n"
                        f"|wRegion:|n {region}\n")
