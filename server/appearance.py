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

hp = "|500"
mana = "|125"
stamina = "|030"
good_damage = "|440"
bad_damage = "|510"
effect = "|405"
good_effect = "|452"
bad_effect = "|411"

character = "|553"
player = "|340"
enemy = "|510"

item = "|545"
gold = "|430"
equipment = "|532"
usable = "|535"
ability = "|035"
spell = "|325"
exit = "|353"
container = "|440"

environments = {
    "grass": {"bg": "|[250", "fg": "|030", "player": "|503"},
    "water": {"bg": "|[004", "fg": "|015", "player": "|r"},
    "rock": {"bg": "|[=g", "fg": "|=e", "player": "|r"},
    "foliage": {"bg": "|[020", "fg": "|320", "player": "|502"},
    "wood": {"bg": "|[320", "fg": "|[100", "player": "|r"},
    "stone": {"bg": "|[=s", "fg": "|=m", "player": "|r"},
}
door = "|[210"


def dmg_color(receiver):
    return bad_damage if receiver.db.hostile_to_players else good_damage
