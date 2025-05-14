Region → Zone → Locality → Area → Room

Each stores its parent and its children.
Recommended level is defined by area, with the recommended level for higher-level locations defined by the minimum of
    their children.
Weather is defined by zone.

To create and set, start from the smallest location and go up to the highest level being created.
    1. Dig new room and stand in it 
    2. "locations/create area = <name>": 
            Creates the global script for the area, and adds the current room. Assigns the
            locality of adjacent rooms to the area (this can be changed) if adjacent rooms share a single locality. 
            If not, and the current locality is wanted: "locations/set <locality name>"
    3. If also creating a new locality:
            a. "locations/create locality = <new locality name>" creates the locality and assigns it to the current zone. 
            b. "locations/set = <new locality name>" sets the current area's locality.
    4. If also creating a new zone:
            a. "locations/create zone = <new zone name>" creates the zone and assigns it to the current region. 
            b. "locations/set = <new zone name>" sets the current locality's zone.
    4. If also creating a new region:
            a. "locations/create region = <new region name>" creates the region. 
            b. "locations/set = <new zone name>" sets the current locality's zone.