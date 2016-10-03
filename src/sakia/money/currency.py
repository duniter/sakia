import re


def shortened(currency):
    """
    Format the currency name to a short one

    :return: The currency name in a shot format.
    """
    words = re.split('[_\W]+', currency)
    if len(words) > 1:
        short = ''.join([w[0] for w in words])
    else:
        vowels = ('a', 'e', 'i', 'o', 'u', 'y')
        short = currency
        short = ''.join([c for c in short if c not in vowels])
    return short.upper()


def symbol(currency):
    """
    Format the currency name to a symbol one.

    :return: The currency name as a utf-8 circled symbol.
    """
    letter = currency[0]
    u = ord('\u24B6') + ord(letter) - ord('A')
    return chr(u)