ambient = "|=p"
story = "|220"
hint = "|010"
cmd = "|=a|[=m"

notify = "|530"
attention = "|550"
warning = "|[100|500"
moreinfo = "|=g"
highlight = "|353"

say = "|145"
whisper = "|525"

good_damage = "|440"
bad_damage = "|510"
effect = "|405"

character = "|553"
player = "|340"
enemy = "|510"

item = "|545"
equipment = "|532"
usable = "|535"
ability = "|035"
spell = "|325"
exit = "|353"
container = "|440"


def dmg_color(attacker, defender):
    return good_damage if defender.db.hostile else bad_damage
