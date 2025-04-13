from evennia.utils.funcparser import FuncParser, ParsingError, ACTOR_STANCE_CALLABLES


# Callable You and Your overridden to use our capitalization logic
def funcparser_callable_you(
        *args, caller=None, receiver=None, mapping=None, capitalize=False, **kwargs
):
    """
    Usage: $you() or $you(key)

    Replaces with you for the caller of the string, with the display_name
    of the caller for others.

    Keyword Args:
        caller (Object): The 'you' in the string. This is used unless another
            you-key is passed to the callable in combination with `mapping`.
        receiver (Object): The recipient of the string.
        mapping (dict, optional): This is a mapping `{key:Object, ...}` and is
            used to find which object `$you(key)` refers to. If not given, the
            `caller` kwarg is used.
        capitalize (bool): Passed by the You helper, to capitalize you.

    Returns:
        str: The parsed string.

    Raises:
        ParsingError: If `caller` and `receiver` were not supplied.

    Notes:
        The kwargs should be passed the to parser directly.

    Examples:
        This can be used by the say or emote hooks to pass actor stance
        strings. This should usually be combined with the $conj() callable.

        - `With a grin, $you() $conj(jump) at $you(tommy).`

        The caller-object will see "With a grin, you jump at Tommy."
        Tommy will see "With a grin, CharName jumps at you."
        Others will see "With a grin, CharName jumps at Tommy."

    """
    if args and mapping:
        # this would mean a $you(key) form
        caller = mapping.get(args[0], None)

    if not (caller and receiver):
        raise ParsingError("No caller or receiver supplied to $you callable.")

    capitalize = bool(capitalize)
    if caller == receiver:
        return "You" if capitalize else "you"
    return (
        caller.get_display_name(looker=receiver, capital=capitalize)
        if hasattr(caller, "get_display_name")
        else str(caller)
    )


def funcparser_callable_you_capitalize(
        *args, you=None, receiver=None, mapping=None, capitalize=True, **kwargs
):
    """
    Usage: $You() - capitalizes the 'you' output.

    """
    return funcparser_callable_you(
        *args, you=you, receiver=receiver, mapping=mapping, capitalize=capitalize, **kwargs
    )


def funcparser_callable_your(
        *args, caller=None, receiver=None, mapping=None, capitalize=False, **kwargs
):
    """
    Usage: $your() or $your(key)

    Replaces with your for the caller of the string, with the display_name +'s
    of the caller for others.

    Keyword Args:
        caller (Object): The 'your' in the string. This is used unless another
            your-key is passed to the callable in combination with `mapping`.
        receiver (Object): The recipient of the string.
        mapping (dict, optional): This is a mapping `{key:Object, ...}` and is
            used to find which object `$you(key)` refers to. If not given, the
            `caller` kwarg is used.
        capitalize (bool): Passed by the You helper, to capitalize you.

    Returns:
        str: The parsed string.

    Raises:
        ParsingError: If `caller` and `receiver` were not supplied.

    Notes:
        The kwargs should be passed the to parser directly.

    Examples:
        This can be used by the say or emote hooks to pass actor stance
        strings.

        - `$your() pet jumps at $you(tommy).`

        The caller-object will see "Your pet jumps Tommy."
        Tommy will see "CharName's pet jumps at you."
        Others will see "CharName's pet jumps at Tommy."

    """
    if args and mapping:
        # this would mean a $your(key) form
        caller = mapping.get(args[0], None)

    if not (caller and receiver):
        raise ParsingError("No caller or receiver supplied to $your callable.")

    capitalize = bool(capitalize)
    if caller == receiver:
        return "Your" if capitalize else "your"

    name = (
        caller.get_display_name(looker=receiver, capital=capitalize)
        if hasattr(caller, "get_display_name")
        else str(caller)
    )

    return name + "'s"


def funcparser_callable_your_capitalize(
        *args, you=None, receiver=None, mapping=None, capitalize=True, **kwargs
):
    """
    Usage: $Your() - capitalizes the 'your' output.

    """
    return funcparser_callable_your(
        *args, you=you, receiver=receiver, mapping=mapping, capitalize=capitalize, **kwargs
    )


MY_ACTOR_STANCE_CALLABLES = ACTOR_STANCE_CALLABLES
MY_ACTOR_STANCE_CALLABLES["you"] = funcparser_callable_you
MY_ACTOR_STANCE_CALLABLES["You"] = funcparser_callable_you_capitalize
MY_ACTOR_STANCE_CALLABLES["your"] = funcparser_callable_your
MY_ACTOR_STANCE_CALLABLES["Your"] = funcparser_callable_your_capitalize


class MyFuncParser(FuncParser):
    pass
