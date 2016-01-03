from enum import Enum


class ArcStatus(Enum):
    WEAK = 0
    STRONG = 1
    ON_PATH = 2


class NodeStatus:
    NEUTRAL = 0
    HIGHLIGHTED = 1
    SELECTED = 2
    OUT = 4
