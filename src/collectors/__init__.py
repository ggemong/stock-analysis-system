"""
Data collectors package
"""

from .stock_collector import StockDataCollector
from .exchange_collector import ExchangeRateCollector
from .macro_collector import MacroEconomicCollector

# Kimchi premium collector (optional - may not exist in older versions)
try:
    from .kimchi_premium_collector import KimchiPremiumCollector
    __all__ = [
        'StockDataCollector',
        'ExchangeRateCollector',
        'MacroEconomicCollector',
        'KimchiPremiumCollector'
    ]
except ImportError:
    __all__ = [
        'StockDataCollector',
        'ExchangeRateCollector',
        'MacroEconomicCollector'
    ]
    KimchiPremiumCollector = None
