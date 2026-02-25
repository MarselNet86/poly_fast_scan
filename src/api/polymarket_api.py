"""
Polymarket API Client
Handles market search and trade fetching from Polymarket APIs
"""

import requests
from typing import Optional, Tuple, List

# Target trader wallet address (gabagool)
TRADER_ADDRESS = "0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d"

# API endpoints
SEARCH_URL = "https://gamma-api.polymarket.com/public-search"
TRADES_URL = "https://data-api.polymarket.com/trades"


def search_market(query: str, timeout: int = 10) -> Tuple[Optional[dict], Optional[dict]]:
    """
    Search for market by name using Polymarket Search API

    Args:
        query: Market name (e.g., "Bitcoin Up or Down - February 10, 3:15PM-3:30PM ET")
        timeout: Request timeout in seconds

    Returns:
        Tuple of (event, market) dicts or (None, None) if not found
    """
    try:
        resp = requests.get(SEARCH_URL, params={"q": query}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        print(f"Error searching market: {exc}")
        return None, None

    events = data.get("events", []) if isinstance(data, dict) else []
    for event in events:
        markets = event.get("markets") or []
        if markets:
            return event, markets[0]
    return None, None


def fetch_trades(condition_id: str, user_address: str = TRADER_ADDRESS,
                 page_limit: int = 500, timeout: int = 15) -> List[dict]:
    """
    Fetch all trades for a condition/user with pagination

    Args:
        condition_id: Market condition ID
        user_address: Trader wallet address
        page_limit: Trades per API call
        timeout: Request timeout

    Returns:
        List of trade dicts (all pages combined)
    """
    all_trades = []
    offset = 0

    while True:
        params = {
            "limit": page_limit,
            "offset": offset,
            "takerOnly": "false",
            "market": condition_id,
            "user": user_address,
        }
        try:
            resp = requests.get(TRADES_URL, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            print(f"Error fetching trades: {exc}")
            return []

        if isinstance(data, dict):
            batch = data.get("trades", [])
        elif isinstance(data, list):
            batch = data
        else:
            batch = []

        all_trades.extend(batch)
        if len(batch) < page_limit:
            break
        offset += page_limit

    return all_trades


def parse_trades(raw_trades: List[dict]) -> List[dict]:
    """
    Parse raw API trades into standardized format

    Args:
        raw_trades: List of raw trade dicts from API

    Returns:
        List of dicts with keys: {type, side, price, shares, cost, timestamp}
    """
    parsed = []

    for item in raw_trades:
        entry = {}
        raw_side = item.get("side", "BUY").upper()
        entry["type"] = "Buy" if raw_side == "BUY" else "Sell"
        entry["side"] = item.get("outcome", "Up")  # "Up" or "Down"
        entry["price"] = float(item.get("price", 0)) * 100.0  # Convert to cents
        entry["shares"] = float(item.get("size", 0))
        entry["cost"] = float(item.get("price", 0)) * entry["shares"]
        entry["timestamp"] = int(item.get("timestamp", 0))
        parsed.append(entry)

    # Sort by timestamp
    parsed.sort(key=lambda x: x["timestamp"])
    return parsed
