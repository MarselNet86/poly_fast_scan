"""
Filename and CSV Datetime Parser
Extracts game datetime from CSV data to build market query
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def extract_game_datetime_from_csv(df: pd.DataFrame) -> Optional[datetime]:
    """
    Extract game END datetime from CSV, then calculate START time

    Strategy:
    1. Read first row's 'timestamp_et' and 'seconds_till_end'
    2. Parse timestamp_et to get current snapshot time
    3. Add seconds_till_end to get game END time
    4. Subtract 15 minutes to get game START time

    Args:
        df: DataFrame with CSV data

    Returns:
        datetime object representing game START time (ET timezone)
    """
    if 'timestamp_et' not in df.columns or 'seconds_till_end' not in df.columns:
        return None

    try:
        # Get first row
        first_row = df.iloc[0]

        # Parse timestamp_et (format: "2026-02-10 03:18:45.179")
        timestamp_str = str(first_row['timestamp_et'])
        snapshot_time = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')

        # Calculate game end time
        seconds_till_end = int(first_row['seconds_till_end'])
        game_end_time = snapshot_time + timedelta(seconds=seconds_till_end)

        # Calculate game start time (15 minutes before end)
        game_start_time = game_end_time - timedelta(minutes=15)

        return game_start_time

    except (ValueError, KeyError, TypeError) as e:
        print(f"Error parsing game datetime: {e}")
        return None


def build_market_query(dt: datetime) -> str:
    """
    Build Polymarket market search query from datetime

    Args:
        dt: Game start datetime (ET timezone)

    Returns:
        Query string like "Bitcoin Up or Down - February 10, 3:15PM-3:30PM ET"
    """
    # Format month and day
    month = dt.strftime('%B')  # "February"
    day = dt.day  # 10

    # Format start time
    start_hour = dt.hour % 12 or 12  # Convert 0-23 to 1-12
    start_minute = dt.minute
    start_ampm = 'AM' if dt.hour < 12 else 'PM'

    # Calculate end time (15 minutes later)
    end_dt = dt + timedelta(minutes=15)
    end_hour = end_dt.hour % 12 or 12
    end_minute = end_dt.minute
    end_ampm = 'AM' if end_dt.hour < 12 else 'PM'

    # Build query
    query = (
        f"Bitcoin Up or Down - "
        f"{month} {day}, "
        f"{start_hour}:{start_minute:02d}{start_ampm}-"
        f"{end_hour}:{end_minute:02d}{end_ampm} ET"
    )

    return query
