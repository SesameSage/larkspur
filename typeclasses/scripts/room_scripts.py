def update_weather(region):
    for area in region.areas:
        for room in area:
            if room.db.outdoors:
                room.print_ambient()

# TODO: Time of day
