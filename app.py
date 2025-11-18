"""
Flask Web Application for MLB Trade Analyzer
"""
from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_collector import MLBDataCollector
from player_valuation import PlayerValuation
from trade_analyzer import TradeAnalyzer

app = Flask(__name__)

# Global variables to store data
players_df = None
valuation = None
analyzer = None

def initialize_app():
    """Initialize the application data"""
    global players_df, valuation, analyzer
    
    data_file = 'data/players_2025.csv'
    
    # Load or collect data
    if os.path.exists(data_file):
        print("Loading existing player data...")
        players_df = pd.read_csv(data_file)
    else:
        print("Collecting player data...")
        collector = MLBDataCollector()
        players_df = collector.collect_all_players_2025()
        collector.save_data(players_df)
    
    # Initialize valuation and analyzer
    print("Initializing valuation system...")
    valuation = PlayerValuation(players_df)
    valuation.calculate_all_values()
    
    analyzer = TradeAnalyzer(valuation)
    print("Application initialized successfully!")

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/teams')
def get_teams():
    """Get all unique teams"""
    teams = sorted(players_df['Team'].unique().tolist())
    return jsonify(teams)

@app.route('/api/players')
def get_players():
    """Get all players or search by query"""
    query = request.args.get('query', '').lower()
    
    if query:
        # Search for players matching query
        mask = players_df['Name'].str.lower().str.contains(query, na=False)
        filtered = players_df[mask]
    else:
        filtered = players_df
    
    # Convert to list of dicts
    players_list = []
    for idx, player in filtered.head(100).iterrows():  # Limit to 100 results
        players_list.append({
            'name': player['Name'],
            'team': player['Team'],
            'position': player['Position'],
            'age': int(player['Age']),
            'playerType': player['PlayerType'],
            'war': float(player.get('WAR', 0)),
            'value': float(player.get('Value', 0))
        })
    
    return jsonify(players_list)

@app.route('/api/team/<team_abbr>')
def get_team_roster(team_abbr):
    """Get roster for specific team"""
    team_players = players_df[players_df['Team'] == team_abbr.upper()]
    
    roster = []
    for idx, player in team_players.iterrows():
        roster.append({
            'name': player['Name'],
            'team': player['Team'],
            'position': player['Position'],
            'age': int(player['Age']),
            'playerType': player['PlayerType'],
            'war': float(player.get('WAR', 0)),
            'value': float(player.get('Value', 0))
        })
    
    # Sort by value descending
    roster = sorted(roster, key=lambda x: x['value'], reverse=True)
    
    return jsonify(roster)

@app.route('/api/player/<player_name>')
def get_player_info(player_name):
    """Get detailed info for a specific player"""
    player_info = valuation.get_player_info(player_name)
    
    if not player_info:
        return jsonify({'error': 'Player not found'}), 404
    
    return jsonify(player_info)

@app.route('/api/analyze-trade', methods=['POST'])
def analyze_trade():
    """Analyze a trade scenario"""
    try:
        data = request.json
        team1_players = data.get('team1', [])
        team2_players = data.get('team2', [])
        
        if not team1_players or not team2_players:
            return jsonify({'error': 'Both teams must have at least one player'}), 400
        
        # Calculate trade probability
        result = analyzer.calculate_trade_probability(team1_players, team2_players)
        
        # Get detailed player info
        details = analyzer.get_trade_details(team1_players, team2_players)
        
        # Convert details to JSON-serializable format
        team1_details = []
        for player in details['team1']:
            team1_details.append({
                'Name': player['Name'],
                'Team': player['Team'],
                'Position': player['Position'],
                'Age': int(player['Age']),
                'PlayerType': player['PlayerType'],
                'Value': float(player['Value']),
                'AVG': float(player.get('AVG', 0)) if player['PlayerType'] == 'Batter' else 0,
                'HR': int(player.get('HR', 0)) if player['PlayerType'] == 'Batter' else 0,
                'RBI': int(player.get('RBI', 0)) if player['PlayerType'] == 'Batter' else 0,
                'ERA': float(player.get('ERA', 0)) if player['PlayerType'] == 'Pitcher' else 0,
                'WHIP': float(player.get('WHIP', 0)) if player['PlayerType'] == 'Pitcher' else 0,
                'SO': int(player.get('SO', 0)) if player['PlayerType'] == 'Pitcher' else 0,
                'WAR': float(player.get('WAR', 0))
            })
        
        team2_details = []
        for player in details['team2']:
            team2_details.append({
                'Name': player['Name'],
                'Team': player['Team'],
                'Position': player['Position'],
                'Age': int(player['Age']),
                'PlayerType': player['PlayerType'],
                'Value': float(player['Value']),
                'AVG': float(player.get('AVG', 0)) if player['PlayerType'] == 'Batter' else 0,
                'HR': int(player.get('HR', 0)) if player['PlayerType'] == 'Batter' else 0,
                'RBI': int(player.get('RBI', 0)) if player['PlayerType'] == 'Batter' else 0,
                'ERA': float(player.get('ERA', 0)) if player['PlayerType'] == 'Pitcher' else 0,
                'WHIP': float(player.get('WHIP', 0)) if player['PlayerType'] == 'Pitcher' else 0,
                'SO': int(player.get('SO', 0)) if player['PlayerType'] == 'Pitcher' else 0,
                'WAR': float(player.get('WAR', 0))
            })
        
        return jsonify({
            'probability': result,
            'details': {
                'team1': team1_details,
                'team2': team2_details
            }
        })
    
    except Exception as e:
        print(f"Error in analyze_trade: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh-data', methods=['POST'])
def refresh_data():
    """Refresh player data from MLB"""
    try:
        collector = MLBDataCollector()
        new_players_df = collector.collect_all_players_2025()
        collector.save_data(new_players_df)
        
        # Reinitialize
        initialize_app()
        
        return jsonify({'success': True, 'message': 'Data refreshed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting MLB Trade Analyzer Web Application...")
    initialize_app()
    print("\n" + "="*50)
    print("Server starting at: http://localhost:5000")
    print("Open this URL in your web browser!")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)