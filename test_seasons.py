#!/usr/bin/env python3
"""
Test script for get_latest_season() function to verify year fallback logic
"""

import urllib.request
import re
from datetime import datetime
from config import VALID_SEASONS

def test_get_latest_season():
    """Test the year fallback logic by checking multiple years"""
    current_year = datetime.now().year
    test_years = [current_year - 1, current_year, current_year + 1]
    
    print("Testing season availability across years:")
    print("=" * 50)
    
    for year in test_years:
        print(f"\nTesting year {year}:")
        url = f"https://plainvillearena.com/ajax_update.php?ddname=Year&iYearId={year}"
        
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
            
            season_names = re.findall(r'<seasonname>([^<]+)</seasonname>', content)
            season_ids = re.findall(r'<seasonid>([^<]+)</seasonid>', content)
            
            if season_names:
                print(f"  Available seasons: {season_names}")
                
                valid_found = []
                for season_id, season_name in zip(season_ids, season_names):
                    if season_name.lower() in VALID_SEASONS:
                        valid_found.append(f"{season_name} (ID: {season_id})")
                
                if valid_found:
                    print(f"  Valid seasons: {valid_found}")
                    print(f"  ✅ Would use: {valid_found[0]}")
                else:
                    print(f"  ❌ No valid seasons found")
            else:
                print(f"  ❌ No seasons available")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Testing actual get_latest_season() function:")
    
    # Import and test the actual function
    from generate_schedules import get_latest_season
    season_id = get_latest_season()
    print(f"Function returned season ID: {season_id}")

if __name__ == "__main__":
    test_get_latest_season()
