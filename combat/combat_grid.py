from evennia.utils.evtable import EvTable

from server import appearance
from typeclasses.scripts.scripts import Script

DIRECTIONS = {
    "n": (0, 1),
    "e": (1, 0),
    "s": (0, -1),
    "w": (-1, 0),
    "ne": (1, 1),
    "nw": (-1, 1),
    "se": (1, -1),
    "sw": (-1, -1)
}


class CombatGrid(Script):
    def at_script_creation(self):
        super().at_script_creation()
        self.db.grid = {}
        self.db.turn_handler = self.obj.scripts.get("Combat Turn Handler")[0]

        self.db.objects = self.db.turn_handler.db.fighters
        self.db.effects = []

        self.at_start()

    def at_start(self, **kwargs):
        # Skip calls on server reload - only call after initialization
        if self.db.turn_handler.db.round != 0:
            return

        starter = self.db.turn_handler.db.starter
        start_target = self.db.turn_handler.db.start_target
        starter_distance = self.db.turn_handler.db.starter_distance

        self.set_coords(starter, 0, 0)
        # Place the target of the fight-starting move away from the starter based on the starting move
        self.set_coords(start_target, 0, y=starter_distance)

        for obj in self.db.objects:
            if obj == starter or obj == start_target:
                continue
            if obj.attributes.has("hostile_to_players"):
                if obj.db.hostile_to_players == starter.db.hostile_to_players:
                    x, y = self.find_available_square(
                        origin_x=starter.db.combat_x, origin_y=starter.db.combat_y, exclude=["n"])
                else:
                    x, y = self.find_available_square(origin_x=start_target.db.combat_x,
                                                      origin_y=start_target.db.combat_y)
            else:
                pass  # When/if any non-entity objects are able to be placed in the grid
            self.set_coords(obj, x, y)

    def set_coords(self, obj, x, y):
        """
        Place the object by setting its coordinate attributes and setting the corresponding position on the grid as
        occupied by the object.

        :param obj: The object being placed.
        :param x: The x coordinate of the grid position to place the object in.
        :param y: The y coordinate of the grid position to place the object in.
        """
        # Remove the object from previous grid position
        try:
            origin_x, origin_y = obj.db.combat_x, obj.db.combat_y
            if origin_x is not None and origin_y is not None:
                self.db.grid[(origin_x, origin_y)] = 0
        # Ignore if there weren't previous coordinates (placing for the first time)
        except AttributeError:
            pass

        # Set the object in new position on the grid
        self.db.grid[(x, y)] = obj

        # Set the new coordinate attributes
        obj.db.combat_x = x
        obj.db.combat_y = y

    def get_obj(self, x, y):
        return self.db.grid.get((x, y), 0)

    def print(self):
        if not self.db.grid:
            return "Empty grid"

        min_x = min([coord[0] for coord in self.db.grid])
        max_x = max([coord[0] for coord in self.db.grid])
        min_y = min([coord[1] for coord in self.db.grid])
        max_y = max([coord[1] for coord in self.db.grid])

        y_range = range(max_y + 1, min_y - 2, -1)
        x_range = range(min_x - 1, max_x + 2)

        x_row = []
        for x in x_range:
            x_row.append("|=a+|=l" + str(x) if x >= 0 else "|=l" + str(x))

        table = EvTable(border=None)
        for y in y_range:
            row = ["|=a+|=l" + str(y) if y >= 0 else "|=l" + str(y),]
            for x in x_range:
                occupant = self.get_obj(x, y)
                tile_effect = self.effect_at(x, y)
                if tile_effect:
                    if (tile_effect.attributes.has("seconds_passed")
                            and tile_effect.db.seconds_passed >= (tile_effect.db.duration - 3)):
                        tile_color = ""
                    else:
                        tile_color = tile_effect.db.tile_color
                else:
                    tile_color = ""
                if occupant == 0 or occupant is None:
                    row.append(f"{tile_color}[ ]|n")
                else:
                    row.append(f"{tile_color}[|n{occupant.combat_symbol()}{tile_color}]|n")
            table.add_row(*row)

        table.add_row("  ", *x_row)

        return table

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    def check_collision(self, x, y, displace=False):
        """
        Check if there is already an object here, and handle the collision.
        If 'displace' is true, the moving object will continue to move and the object already in place will be displaced.
        If 'displace' is false, movement will not be able to continue and the original object will stay in place.

        :param x: The x-coordinate of the oncoming square to check.
        :param y: The y-coordinate of the oncoming square to check.
        :param displace: Whether the moving object should displace existing objects, or be stopped by them.
        :return: True if the object's movement is stopped, False if there is no collision or displacement occurred.
        """

        obj_here = self.get_obj(x, y)
        if obj_here == 0:
            return False
        else:
            if displace:
                self.displace(obj_here)
                return False
            else:
                return True

    def check_square(self, direction, obj=None, origin_x=None, origin_y=None, distance=1):
        """
        Returns the contents of the square a given distance and direction from the given object or origin coordinates.

        :param direction: Short cardinal direction from the origin - "n", "e", "sw", etc.
        :param obj: (optional) The object whose position is the origin, if coordinates are not given.
        :param origin_x: (optional) The origin x coordinate, if not giving an object instead.
        :param origin_y: (optional) The origin y coordinate, if not giving an object instead.
        :param distance: The number of squares away in the given direction to check.
        :return: The object occupying the square, 0 if the square is empty, or None if the check failed.
        """
        if not self.validate_direction(direction):
            return
        if origin_x is None or origin_y is None:
            if not self.validate_object(obj):
                return
            origin_x = obj.db.combat_x
            origin_y = obj.db.combat_y

        target_x, target_y = self.get_coords(origin_x, origin_y, direction, distance)

        return self.get_obj(target_x, target_y)

    def displace(self, obj):
        if not self.validate_object(obj):
            return

        x, y = self.find_available_square(obj=obj)
        self.move_to(obj, x, y)

    def distance(self, point1, point2):
        """Returns the Chebyshev distance between the two objects or coordinate sets. This equates to the number of
        single-square moves in any direction that it would take to reach the other square."""
        if isinstance(point1, tuple):
            x1, y1 = point1
        else:
            x1, y1 = point1.db.combat_x, point1.db.combat_y
        if isinstance(point2, tuple):
            x2, y2 = point2
        else:
            x2, y2 = point2.db.combat_x, point2.db.combat_y

        return max(abs(x1 - x2), abs(y1 - y2))

    def effect_at(self, x, y):
        """Return the effect script if there is a tile effect applied to the given coordinates."""
        for effect in self.db.effects:
            if (x, y) in effect.db.tiles:
                return effect

    def find_available_square(self, obj=None, origin_x=None, origin_y=None, exclude=None):
        """
        Find one of the nearest empty squares relative to the given coordinates.

        :param obj: (optional) The object whose position should be referenced, if not giving coordinates.
        :param origin_x: (optional) The x coordinate of the square to reference, if not giving an object.
        :param origin_y: (optional) The y coordinate of the square to reference, if not giving an object.
        :param exclude: A list of directions to exclude from the search.

        :return: The x and y coordinates of an available square.
        """
        if origin_x is None or origin_y is None:
            if not self.validate_object(obj):
                return
            else:
                origin_x = obj.db.combat_x
                origin_y = obj.db.combat_y

        for i in range(1, 5):
            for direction in DIRECTIONS:
                if exclude and direction in exclude:
                    continue
                x, y = self.get_coords(direction=direction, distance=i, origin_x=origin_x, origin_y=origin_y)
                # Return this square if it's empty
                if self.get_obj(x, y) == 0:
                    return x, y

    def get_coords(self, direction, distance, obj=None, origin_x=None, origin_y=None):
        """
        Get the coordinates of the square that is the given distance away in the given direction from the given
        coordinates or the given object's coordinates.

        :param direction: The short cardinal direction ("n", "w", "se", etc.) to look in
        :param distance: The number of squares away in the given direction to get the coordinates for
        :param obj: (optional) The object whose origin should be referenced, if not giving coordinates
        :param origin_x: (optional) The origin x coordinate, if not giving an object instead.
        :param origin_y: (optional) The origin y coordinate, if not giving an object instead.
        :return: The coordinates of the target square.
        """
        if not self.validate_direction(direction):
            return
        if origin_x is None or origin_y is None:
            if not self.validate_object(obj):
                return
            origin_x = obj.db.combat_x
            origin_y = obj.db.combat_y

        delta_x, delta_y = DIRECTIONS[direction]
        target_x = origin_x + (delta_x * distance)
        target_y = origin_y + (delta_y * distance)
        return target_x, target_y

    def handle_move_ap(self, character):
        """Exchanges AP for a number of steps."""
        character.db.combat_stepsleft -= 1
        if character.db.combat_stepsleft == 0:
            self.db.turn_handler.spend_action(character, 1, action_name="move")
            character.db.combat_stepsleft = character.speed()
            if character.db.combat_ap != 0:
                character.msg(
                    f"{appearance.notify}-1 AP, {character.db.combat_ap} left. You may take "
                    f"{character.db.combat_stepsleft} more steps before another action must be spent.")

    def move_to(self, obj, x, y, displace=False, spend=False):
        """
        Move the given object to the given coordinates, if possible. Force other objects out to make it possible if
        displacing.

        :param obj: The object to move.
        :param x: The x-coordinate to move to.
        :param y: The y-coordinate to move to.
        :param displace: If true, displace whatever is there. If false, find somewhere nearby if the square is blocked.
        :param spend: Whether this movement spends a character's AP
        :return: True if movement was successful, False if stopped.
        """
        if not self.validate_object(obj):
            return

        if self.check_collision(x, y, displace):
            obj.msg("The way is blocked!")
            return False
        else:
            self.set_coords(obj, x, y)
            effect = self.effect_at(x, y)
            if effect:
                effect.apply_to(obj)
            if spend:
                self.handle_move_ap(obj)
                if obj.db.combat_ap > 0:
                    obj.msg(self.print())
            else:
                obj.msg(self.print())
            return True

    def step(self, obj, direction, displace=False):
        """
        Move the given object one square at a time in the given direction.

        :param obj: The object to move
        :param direction: The short direction ("n", "w", "se", etc.) to move in
        :param displace: If true, displace objects in the path. If false, the given object is unable to move.
        :return: True if movement was successful, False if stopped.
        """
        if not self.validate_object(obj) or not self.validate_direction(direction):
            return False

        if not obj.is_turn():
            obj.msg("You can only move on your turn!")
            return False

        if obj.db.combat_ap < 1:
            obj.msg("Not enough AP!")
            return False

        target_x, target_y = self.get_coords(origin_x=obj.db.combat_x, origin_y=obj.db.combat_y,
                                             direction=direction, distance=1)

        return self.move_to(obj=obj, x=target_x, y=target_y, displace=displace, spend=True)

    def take_steps(self, obj, direction, distance, displace=False):
        """
        Move the given object the given number of squares in the given distance, if possible.

        :param obj: The object to move
        :param direction: The short direction ("n", "w", "se", etc.) to move in
        :param distance: The number of squares to move the object (if possible)
        :param displace: If true, objects in the moving object's path are displaced. If false, the moving stops if a
        collision happens.
        """
        if not self.validate_object(obj) or not self.validate_direction(direction):
            return

        for move in range(1, distance):
            if not self.step(obj, direction, displace):
                break  # Stop trying to move if blocked

    def validate_direction(self, direction):
        """Make sure the given direction is a recognized short direction string."""
        if direction not in DIRECTIONS:
            self.obj.msg_contents(f"{appearance.warning} Invalid grid direction! ({direction})")
            return False
        else:
            return True

    def validate_object(self, obj):
        """Make sure the given object is an object stored in the grid."""
        if obj not in self.db.objects:
            self.obj.msg_contents(appearance.warning + "Grid object not found!")
            return False
        else:
            return True
