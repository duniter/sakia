

def timestamp_to_dhms(ts):
    days, remainder = divmod(ts, 3600 * 24)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return days, hours, minutes, seconds