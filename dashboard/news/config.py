"""Configuration constants for Commodity News Analysis."""

# =============================================================================
# COMMODITY DEFINITIONS
# =============================================================================

COMMODITIES = {
    'Gold': {
        'keywords': ['gold', 'bullion', 'precious metal', 'xau', 'gold price', 'gold futures'],
        'etf_symbols': ['GLD', 'IAU', 'SGOL'],
        'symbol': 'GCUSD',
        'emoji': '🥇'
    },
    'Silver': {
        'keywords': ['silver', 'xag', 'silver price', 'silver futures', 'precious metal'],
        'etf_symbols': ['SLV', 'SIVR'],
        'symbol': 'SIUSD',
        'emoji': '🥈'
    },
    'Copper': {
        'keywords': ['copper', 'copper price', 'copper futures', 'base metal', 'industrial metal'],
        'etf_symbols': ['CPER', 'JJC'],
        'symbol': 'HGUSD',
        'emoji': '🔶'
    },
    'Wheat': {
        'keywords': ['wheat', 'grain', 'wheat futures', 'wheat price', 'agriculture', 'crop'],
        'etf_symbols': ['WEAT'],
        'symbol': 'ZWUSD',
        'emoji': '🌾'
    },
    'Oats': {
        'keywords': ['oats', 'oat futures', 'oat price', 'grain', 'cereal'],
        'etf_symbols': [],
        'symbol': 'ZOUSD',
        'emoji': '🌾'
    }
}

# =============================================================================
# TAG DEFINITIONS
# =============================================================================

TAG_KEYWORDS = {
    'Supply': ['supply', 'production', 'output', 'mine', 'mining', 'harvest', 'shortage', 'surplus'],
    'Demand': ['demand', 'consumption', 'import', 'export', 'buying', 'purchase'],
    'Policy': ['fed', 'federal reserve', 'central bank', 'interest rate', 'policy', 'regulation', 'tariff'],
    'Weather': ['weather', 'drought', 'flood', 'storm', 'frost', 'climate'],
    'Geopolitical': ['war', 'conflict', 'sanction', 'trade war', 'tension', 'geopolitical', 'ukraine', 'russia', 'china'],
    'Market': ['price', 'futures', 'rally', 'decline', 'surge', 'drop', 'market', 'trading', 'investor'],
    'Currency': ['dollar', 'usd', 'currency', 'forex', 'exchange rate'],
}

TAG_COLORS = {
    'Supply': 'tag-supply',
    'Demand': 'tag-demand',
    'Policy': 'tag-policy',
    'Weather': 'tag-weather',
    'Geopolitical': 'tag-geopolitical',
    'Market': 'tag-market',
    'Currency': 'tag-currency'
}

# =============================================================================
# UI STYLING
# =============================================================================

COMMODITY_BADGES = {
    'Gold': 'badge-gold',
    'Silver': 'badge-silver',
    'Copper': 'badge-copper',
    'Wheat': 'badge-wheat',
    'Oats': 'badge-oats',
    'General': 'badge-general'
}
