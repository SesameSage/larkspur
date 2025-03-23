ambient = "|=p"
story = "|220"
hint = "|010"
notify = "|530"
attention = "|550"
warning = "|[100|500"
moreinfo = "|=g"

say = "|145"
whisper = "|525"

cmd = "|=a|[=m"
good_damage = "|440"
bad_damage = "|510"

character = "|553"
player = "|340"
enemy = "|400"

item = "|545"
equipment = "|224"
ability = "|025"
spell = "|315"


def dmg_color(attacker, defender):
    return good_damage if defender.db.hostile else bad_damage
