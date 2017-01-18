import re


def timestamp_to_dhms(ts):
    days, remainder = divmod(ts, 3600 * 24)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return days, hours, minutes, seconds


def detect_non_printable(data):
    control_chars = ''.join(map(chr, list(range(0, 32)) + list(range(127, 160))))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    if control_char_re.search(data):
        return True
