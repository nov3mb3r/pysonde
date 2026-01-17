#!/usr/bin/env python3
import argparse
import requests
from datetime import datetime, timedelta, timezone
import sys
import re

VALID_STATIONS = ['AT138', 'EB040', 'SO148', 'JR053', 'MD031', 'NA325']

# IARU Region 1 Ham Band allocations (MHz)
HAM_BANDS = {
    '160m': (1.8, 2.0),
    '80m': (3.5, 3.8), 
    '60m': (5.3, 5.4),
    '40m': (7.0, 7.2),
    '30m': (10.1, 10.15),
    '20m': (14.0, 14.35),
    '17m': (18.068, 18.168),
    '15m': (21.0, 21.45),
    '12m': (24.89, 24.99),
    '10m': (28.0, 29.7)
}

def parse_lookback(lookback_str):
    match = re.match(r'^(\d+)([dhm])$', lookback_str.lower())
    if not match:
        raise ValueError("Format: 1d, 6h, 30m")
    value, unit = int(match.group(1)), match.group(2)
    if unit == 'd': return timedelta(days=value)
    if unit == 'h': return timedelta(hours=value)
    if unit == 'm': return timedelta(minutes=value)
    raise ValueError("Unit must be d/h/m")

def is_valid_value(val):
    try:
        f = float(val)
        return 0.1 <= f <= 50.0
    except:
        return False

def get_recommended_bands(muf, fof2, fmin):
    """Return perfectly formatted, aligned ham band recommendations."""
    muf_mhz = float(muf) if is_valid_value(muf) else 0
    fof2_mhz = float(fof2) if is_valid_value(fof2) else 0
    fmin_mhz = float(fmin) if is_valid_value(fmin) else 3.0
    
    recommended = []
    
    for band, (low, high) in HAM_BANDS.items():
        band_center = (low + high) / 2
        
        if fmin_mhz > low:
            status = "🔴 ABSORBED "
        elif band_center < muf_mhz * 0.85:
            status = "🟢 OPEN  "
        elif band_center < fof2_mhz * 1.3:
            status = "🟢 NVIS    " 
        elif band_center < muf_mhz * 0.95:
            status = "🟡 MARGINAL"
        else:
            status = "🔴 CLOSED  "
        
        band_str = f"{band:>4} ({low:>4.1f}-{high:>4.1f} MHz)"
        recommended.append(f"{band_str}: {status}")
    
    return recommended

def find_best_data(items):
    for item in reversed(items):
        scaled = item.get('scaled', {})
        muf = scaled.get('mufD')
        fof2 = scaled.get('foF2')
        if is_valid_value(muf) and is_valid_value(fof2):
            return item
    return None

def fetch_ionogram_data(station='AT138', lookback='10m'):
    now_utc = datetime.now(timezone.utc)
    
    if lookback == '10m':
        start_time = now_utc - timedelta(minutes=10)
        end_time = now_utc
    else:
        target_time = now_utc - parse_lookback(lookback)
        start_time = target_time - parse_lookback(lookback)
        end_time = target_time + timedelta(minutes=15)
    
    url = "https://electron.space.noa.gr/ionostream/api/v2/idb/sao/pager"
    params = {
        'station': station,
        'start': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'end': end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'limit': 100
    }
    
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    items = data.get('items', [])
    
    if not items:
        raise ValueError(f"No data for {station}")
    
    best_item = find_best_data(items)
    if not best_item:
        raise ValueError(f"No valid data for {station}")
    
    dataset = best_item.get('dataset', {})
    scaled = best_item.get('scaled', {})
    
    return (
        dataset.get('timestamp', 'N/A').replace('Z', ''),
        scaled.get('mufD', 'N/A'),
        scaled.get('foF2', 'N/A'),
        scaled.get('fmin', 'N/A'),
        station
    )

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="DIAS Ionogram Data Fetcher + Ham Band Advisor",
        epilog="""
USAGE EXAMPLES:
  %(prog)s                    # Latest AT138 data (last 10min)
  %(prog)s -s EB040          # Ebre station (Spain)
  %(prog)s -lb 1h            # Data closest to 1hr ago
  %(prog)s -s JR053 -lb 6h   # Juliusruh, 6hrs ago

ARGUMENTS:
  -s, --station  STATION     Ionosonde station (default: AT138)
  -lb, --lookback LOOKBACK   Time ago to target (default: 10m)
  
LOOKBACK FORMAT: 1d=1day, 6h=6hours, 30m=30minutes

STATIONS:
  AT138=Athens GR, EB040=Ebre ES, SO148=Sopron HU, JR053=Juliusruh DE
        """
    )
    parser.add_argument('-s', '--station', default='AT138',
                       help="Ionosonde station (default: AT138)")
    parser.add_argument('-lb', '--lookback', default='10m',
                       help="Lookback time (default: 10m). Format: 1d,6h,30m")
    
    args = parser.parse_args()

    try:
        data_timestamp, muf, fof2, fmin, station = fetch_ionogram_data(args.station, args.lookback)
        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        print("\n" + "="*50)
        print(f"IONOGRAM DATA - {station}")
        print("="*50 + "\n")
        
        print(f"Station:        {station}".ljust(28))
        print()
        print(f"Current time:   {current_time}".ljust(28))
        print(f"Data timestamp: {data_timestamp}".ljust(28))
        print()
        print(f"MUF:            {muf} MHz".ljust(28))
        print(f"FoF2 (NVIS):    {fof2} MHz".ljust(28))
        print(f"fmin:           {fmin} MHz".ljust(28))
        print()
        
        print("AVAILABLE BANDS (IARU R1):")
        print("-" * 50)
        bands = get_recommended_bands(muf, fof2, fmin)
        for band_info in bands:
            print(f"  {band_info}")
        
        print("\n" + "="*50)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Try: python3 pysonde.py -s EB040 -lb 1d", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
