import re
import hashlib
from PyQt5.QtCore import QSharedMemory
from PyQt5.QtWidgets import QApplication


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


def single_instance_lock(currency):
    key = hashlib.sha256(currency.encode('utf-8')
                         + "77rWEV37vupNhQs6ktDREthqSciyV77OYrqPBSwV755JFIhl9iOywB7G5DkAKU8Y".encode('utf-8'))\
        .hexdigest()
    sharedMemory = QSharedMemory(key)
    if sharedMemory.attach(QSharedMemory.ReadOnly):
        sharedMemory.detach()
        return None

    if sharedMemory.create(1):
        return sharedMemory

    return None


def cleanup_lock(lock):
    if lock.isAttached():
        lock.detach()


def attrs_tuple_of_str(ls):
    if isinstance(ls, tuple):
        return ls
    elif isinstance(ls, list):
        return tuple([str(a) for a in ls])
    elif isinstance(ls, str):
        if ls:  # if string is not empty
            return tuple([str(a) for a in ls.split('\n')])
        else:
            return tuple()


def dpi_ratio():
    screen = QApplication.screens()[0]
    dotsPerInch = screen.logicalDotsPerInch()
    return dotsPerInch / 96
