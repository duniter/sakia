import re
from PyQt5.QtCore import QSharedMemory


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


def single_instance_lock():
    sharedMemory = QSharedMemory("77rWEV37vupNhQs6ktDREthqSciyV77OYrqPBSwV755JFIhl9iOywB7G5DkAKU8Y")
    if sharedMemory.attach(QSharedMemory.ReadOnly):
        sharedMemory.detach()
        return None

    if sharedMemory.create(1):
        return sharedMemory

    return None


def cleanup_lock(lock):
    if lock.isAttached():
        lock.detach()
