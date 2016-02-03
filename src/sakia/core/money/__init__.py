from .quantitative import Quantitative
from .relative import Relative
from .quant_zerosum import QuantitativeZSum
from .relative_zerosum import RelativeZSum
from .relative_to_past import RelativeToPast
from .dividend_per_day import DividendPerDay

Referentials = (Quantitative, Relative, QuantitativeZSum, RelativeZSum, RelativeToPast, DividendPerDay)
