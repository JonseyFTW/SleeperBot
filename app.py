from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Function to get rosters for the league
def get_rosters(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    response = requests.get(url)
    return response.json()

# Function to get users for the league
def get_users(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}/users"
    response = requests.get(url)
    return response.json()

# Function to map team names to roster IDs
def get_team_name_by_roster_id(rosters, users):
    owner_to_team_name = {user['user_id']: user['metadata'].get('team_name', user['display_name']) for user in users}
    roster_to_team_name = {}
    for roster in rosters:
        owner_id = roster['owner_id']
        team_name = owner_to_team_name.get(owner_id, 'Unknown Team')
        roster_to_team_name[roster['roster_id']] = team_name
    return roster_to_team_name

# Function to get weekly matchups for the league
def get_weekly_matchups(league_id, week):
    url = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
    response = requests.get(url)
    return response.json()

# Function to map player IDs to player names
def map_player_ids(player_ids):
    url = "https://sleeperplayermapping-bbepc9crdbe8e8du.centralus-01.azurewebsites.net/map_player_ids"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "player_ids": player_ids
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {player_id: "Unknown Player" for player_id in player_ids}

# Function to generate results with team matchups and player names
def generate_results_with_teams(league_id, week):
    rosters = get_rosters(league_id)
    users = get_users(league_id)
    roster_to_team_name = get_team_name_by_roster_id(rosters, users)
    matchups = get_weekly_matchups(league_id, week)
    organized_matchups = {}

    for team in matchups:
        matchup_id = team['matchup_id']
        if matchup_id not in organized_matchups:
            organized_matchups[matchup_id] = []
        organized_matchups[matchup_id].append({
            'team_name': roster_to_team_name.get(team['roster_id'], 'Unknown Team'),
            'points': team['points'],
            'players': team['starters']
        })

    results = []
    for matchup_id, teams in organized_matchups.items():
        if len(teams) == 2:
            team1, team2 = teams
            winner = team1 if team1['points'] > team2['points'] else team2
            loser = team2 if team1['points'] > team2['points'] else team1
            key_players = map_player_ids(team1['players'][:2] + team2['players'][:2])
            player_names = list(key_players.values())
            results.append(f"{team1['team_name']} ({team1['points']} points) vs {team2['team_name']} ({team2['points']} points) "
                           f"- Winner: {winner['team_name']}. Star performances by {player_names[0]} and {player_names[1]}.")
    
    return results

# Function to generate matchups without points but with players
def generate_matchups_with_players(league_id, week):
    rosters = get_rosters(league_id)
    users = get_users(league_id)
    roster_to_team_name = get_team_name_by_roster_id(rosters, users)
    matchups = get_weekly_matchups(league_id, week)
    organized_matchups = {}

    for team in matchups:
        matchup_id = team['matchup_id']
        if matchup_id not in organized_matchups:
            organized_matchups[matchup_id] = []
        organized_matchups[matchup_id].append({
            'team_name': roster_to_team_name.get(team['roster_id'], 'Unknown Team'),
            'players': team['starters']  # Store player IDs for this team
        })

    results = []
    for matchup_id, teams in organized_matchups.items():
        if len(teams) == 2:
            team1, team2 = teams
            # Map player IDs to player names for both teams
            key_players = map_player_ids(team1['players'] + team2['players'])
            team1_player_names = [key_players[player_id] for player_id in team1['players']]
            team2_player_names = [key_players[player_id] for player_id in team2['players']]

            # Prepare matchup result without points, but with players
            results.append(f"{team1['team_name']} vs {team2['team_name']} - Players: {', '.join(team1_player_names)} vs {', '.join(team2_player_names)}")

    return results

# Endpoint to trigger the function
@app.route('/generate_results', methods=['POST'])
def generate_results():
    data = request.json
    league_id = data.get('league_id')
    week = data.get('week')

    if not league_id or not week:
        return jsonify({"error": "Invalid input. 'league_id' and 'week' are required."}), 400

    results = generate_results_with_teams(league_id, week)
    return jsonify(results)

# New route for league matchups without points but with players
@app.route('/get_league_matchups', methods=['POST'])
def get_league_matchups():
    data = request.json
    league_id = data.get('league_id')
    week = data.get('week')

    if not league_id or not week:
        return jsonify({"error": "Invalid input. 'league_id' and 'week' are required."}), 400

    results = generate_matchups_with_players(league_id, week)
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
