import random


def update_weather(region):
    weather = random.choice(region.weathers)
    for area in region.areas:
        for room in area:
            if room.db.outdoors:
                room.print_ambient(weather["desc"])

# TODO: Time of day
