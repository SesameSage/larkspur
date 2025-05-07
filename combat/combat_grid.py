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
        self.db.grid = [[]]
        self.db.turn_handler = self.obj.scripts.get("TurnHandler")[0]
        self.db.objects = []

    def at_start(self, **kwargs):
        # Skip calls on server reload - only call after initialization
        if self.db.turn_handler.db.round != 0:
            return

        starter = self.db.turn_handler.db.starter
        self.set_coords(starter, 0, 0)

    def set_coords(self, obj, x, y):
        """
        Place the object by setting its coordinate attributes and setting the corresponding position on the grid as
        occupied by the object.

        :param obj: The object being placed.
        :param x: The x coordinate of the grid position to place the object in.
        :param y: The y coordinate of the grid position to place the object in.
        """
        obj.db.combat_x = x
        obj.db.combat_y = y
        self.db.grid[x][y] = obj

    def check_collision(self, obj, x, y, displace=False):
        """
        Check if there is already an object here, and handle the collision.
        If 'displace' is true, the moving object will continue to move and the object already in place will be displaced.
        If 'displace' is false, movement will not be able to continue and the original object will stay in place.

        :param obj: The object being moved.
        :param x: The x-coordinate of the oncoming square to check.
        :param y: The y-coordinate of the oncoming square to check.
        :param displace: Whether the moving object should displace existing objects, or be stopped by them.
        """
        if not self.validate_object(obj):
            return

        obj_here = self.db.grid[x][y]
        if obj_here:
            if displace:
                displaced_obj = obj_here
            else:
                displaced_obj = obj
            self.displace(displaced_obj)

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

        return self.db.grid[target_x][target_y]

    def displace(self, obj, direction=None):
        # TODO: Displace
        if not self.validate_object(obj) or not self.validate_direction(direction):
            return

        pass

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

    def move(self, obj, direction, displace=False):
        """
        Move the given object one square at a time in the given direction.

        :param obj: The object to move
        :param direction: The short direction ("n", "w", "se", etc.) to move in
        :param displace: If true, displace objects in the path. If false, the given object is unable to move.
        """
        if not self.validate_object(obj) or not self.validate_direction(direction):
            return

        target_x, target_y = self.get_coords(origin_x=obj.db.combat_x, origin_y=obj.db.combat_y,
                                             direction=direction, distance=1)

        self.move_to(obj=obj, x=target_x, y=target_y, displace=displace)

    def multi_move(self, obj, direction, distance, displace=False):
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
            self.move(obj, direction, displace)

    def move_to(self, obj, x, y, displace=False):
        """
        Move the given object to the given coordinates, if possible. If not possible and not displacing, move nearby.

        :param obj: The object to move.
        :param x: The x-coordinate to move to.
        :param y: The y-coordinate to move to.
        :param displace: If true, displace whatever is there. If false, find somewhere nearby if the square is blocked.
        """
        if not self.validate_object(obj):
            return

        self.check_collision(obj, x, y, displace)
        self.set_coords(obj, x, y)

    def validate_direction(self, direction):
        """Make sure the given direction is a recognized short direction string."""
        if direction not in DIRECTIONS:
            self.obj.msg_contents(appearance.warning + "Invalid grid direction!")
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
