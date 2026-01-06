import urllib.request
import urllib.parse
import re
from datetime import datetime, timedelta
from config import TARGET_TEAMS, VALID_SEASONS, ARENA_NAME, ARENA_ADDRESS, GITHUB_PAGES_URL

# ============================================================================
# MAIN SCRIPT - Configuration loaded from config.py
# ============================================================================

def get_latest_season():
    """Get the most recent season, trying current year, next year, then previous year"""
    current_year = datetime.now().year
    
    # Try current year, next year, then previous year
    for year in [current_year, current_year + 1, current_year - 1]:
        url = f"https://plainvillearena.com/ajax_update.php?ddname=Year&iYearId={year}"
        
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
            
            # Filter for standard seasons only
            season_names = re.findall(r'<seasonname>([^<]+)</seasonname>', content)
            season_ids = re.findall(r'<seasonid>([^<]+)</seasonid>', content)
            
            for season_id, season_name in zip(season_ids, season_names):
                if season_name.lower() in VALID_SEASONS:
                    print(f"Using {year} {season_name} season (ID: {season_id})")
                    return season_id
        except:
            continue
    
    print("No valid seasons found, using fallback")
    return '95'  # fallback

def get_divisions(season_id):
    """Get all divisions for a season"""
    url = f"https://plainvillearena.com/getdivision.php?seasonid={season_id}"
    
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
    
    names = re.findall(r'<divisionname>([^<]+)</divisionname>', content)
    ids = re.findall(r'<divisionid>([^<]+)</divisionid>', content)
    return list(zip(ids, names))

def get_schedules(division_id):
    """Get schedules for a division"""
    url = f"https://plainvillearena.com/sspanel/getSchedule.php?divid={division_id}"
    
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
    
    names = re.findall(r'<schedulename>([^<]+)</schedulename>', content)
    ids = re.findall(r'<scheduleid>([^<]+)</scheduleid>', content)
    return list(zip(ids, names))

def get_teams(division_id, schedule_id):
    """Get all teams for a division/schedule"""
    url = f"https://plainvillearena.com/sspanel/getTeam.php?divisionid={division_id}&scheduleid={schedule_id}"
    
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
    
    return re.findall(r'<teamname>([^<]+)</teamname>', content)

def get_team_schedule_ical(team_name, division_id, season_id, schedule_id):
    """Generate iCal for a specific team"""
    data = {
        'searchYear': str(datetime.now().year),
        'iSSSeasonId': season_id,
        'iDivisionId': division_id,
        'iScheduleId': schedule_id,
        'vTeamName': team_name,
        'btn_search_x': '54',
        'btn_search_y': '22',
        'btn_search': ''
    }
    
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request('https://plainvillearena.com/schedules.html', data=encoded_data, method='POST')
    
    with urllib.request.urlopen(req) as response:
        csv_content = response.read().decode('utf-8')
    
    lines = csv_content.strip().split('\n')
    ical_content = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{team_name} Schedule//EN"]
    
    for i, line in enumerate(lines[2:]):
        if line.strip():
            parts = line.split(',')
            if len(parts) >= 7:
                date_str, day, time_str, season, division, location, teams = parts[:7]
                
                try:
                    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
                    end_dt = dt + timedelta(hours=1)
                    
                    # Create unique UID using team, year, season, and game number
                    current_year = datetime.now().year
                    uid_string = f"{team_name}-{current_year}-{season}-{i}"
                    
                    ical_content.extend([
                        "BEGIN:VEVENT",
                        f"UID:{uid_string}@plainville",
                        f"DTSTART;TZID=America/New_York:{dt.strftime('%Y%m%dT%H%M%S')}",
                        f"DTEND;TZID=America/New_York:{end_dt.strftime('%Y%m%dT%H%M%S')}",
                        f"SUMMARY:{division} - {team_name}",
                        f"LOCATION:{ARENA_NAME}, {ARENA_ADDRESS}",
                        f"DESCRIPTION:{season} Season - {division} Division",
                        "END:VEVENT"
                    ])
                except ValueError:
                    continue
    
    ical_content.append("END:VCALENDAR")
    return '\n'.join(ical_content)

# Configuration - map divisions to specific teams
TARGET_TEAMS = {
    'F1R': ['HOOLIGANS'],
    'F2': ['SCREAMING MONKEYS']
}

# Get latest season
season_id = get_latest_season()
print(f"Using season ID: {season_id}")

# Get all divisions
all_divisions = get_divisions(season_id)
print(f"Found {len(all_divisions)} divisions")

# Process target divisions
for division_id, division_name in all_divisions:
    if division_name in TARGET_TEAMS:
        print(f"\nProcessing {division_name} (ID: {division_id})")
        
        # Get schedules for this division
        schedules = get_schedules(division_id)
        
        for schedule_id, schedule_name in schedules:
            # Skip playoff schedules for now since they don't have proper team names
            if "PLAYOFF" in schedule_name.upper():
                print(f"  Skipping playoff schedule: {schedule_name}")
                continue
                
            print(f"  Schedule: {schedule_name}")
            
            # Get teams for this schedule
            teams = get_teams(division_id, schedule_id)
            print(f"  Found {len(teams)} teams")
            
            # Generate calendar for specified teams in this division
            target_teams_for_division = TARGET_TEAMS[division_name]
            
            for team in teams:
                # Skip if specific teams specified and this team not in list
                if target_teams_for_division and team not in target_teams_for_division:
                    continue
                    
                try:
                    ical_data = get_team_schedule_ical(team, division_id, season_id, schedule_id)
                    filename = f'{division_name}_{team.replace(" ", "_")}.ics'
                    
                    with open(filename, 'w') as f:
                        f.write(ical_data)
                    print(f"    Generated {filename}")
                    
                except Exception as e:
                    print(f"    Error generating {team}: {e}")

print("\nDone! Generated calendars for all teams in target divisions.")

# Generate index.html with actual teams found
html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Plainville Arena Team Schedules</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .division { margin: 20px 0; }
        .team-link { display: block; margin: 5px 0; padding: 8px; background: #f5f5f5; text-decoration: none; color: #333; border-radius: 4px; }
        .team-link:hover { background: #e5e5e5; }
    </style>
</head>
<body>
    <h1>Plainville Arena Team Schedules</h1>
    <p>Choose how to add calendars:</p>
    <ul>
        <li><strong>📥 Download</strong> - Download .ics file to import once</li>
        <li><strong>📅 Google Calendar</strong> - Subscribe for automatic updates</li>
        <li><strong>🍎 Apple Calendar</strong> - Subscribe for automatic updates</li>
        <li><strong>Subscribe URL</strong> - Copy/paste into other calendar apps</li>
    </ul>
    
'''

# Group generated files by division
import os
generated_files = [f for f in os.listdir('.') if f.endswith('.ics')]
divisions = {}

for filename in generated_files:
    if '_' in filename:
        division = filename.split('_')[0]
        team = filename.replace('.ics', '').replace(f'{division}_', '').replace('_', ' ')
        
        if division not in divisions:
            divisions[division] = []
        divisions[division].append((team, filename))

# Generate HTML for each division
for division in sorted(divisions.keys()):
    html_content += f'    <div class="division">\n        <h2>{division} Division</h2>\n'
    
    for team, filename in sorted(divisions[division]):
        # Create subscription URLs
        base_url = f"{GITHUB_PAGES_URL}/{filename}"
        google_url = f"https://calendar.google.com/calendar/render?cid={base_url}"
        
        html_content += f'''        <div style="margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px;">
            <strong>{division} - {team}</strong><br>
            <a href="{filename}" style="margin-right: 15px;">📥 Download</a>
            <a href="https://calendar.google.com/calendar/render?cid={base_url}" target="_blank" style="margin-right: 15px;">📅 Add to Google Calendar</a>
            <a href="webcal://{base_url.replace('https://', '')}" style="margin-right: 15px;">🍎 Add to Apple Calendar</a>
            <small style="display: block; margin-top: 5px; color: #666;">Subscribe URL: {base_url}</small>
        </div>
'''
    
    html_content += '    </div>\n\n'

html_content += '''    <p><small>Schedules update daily at 6 AM EST</small></p>
</body>
</html>'''

with open('index.html', 'w') as f:
    f.write(html_content)

print("Updated index.html with generated teams")
