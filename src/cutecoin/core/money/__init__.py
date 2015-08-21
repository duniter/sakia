from enum import Enum

class RefType(Enum):
    q = 0
    r = 1

from .quantitative import Quantitative
from .relative import Relative
from .quant_zerosum import QuantitativeZSum
from .relative_zerosum import RelativeZSum

Referentials = (Quantitative, Relative, QuantitativeZSum, RelativeZSum)
