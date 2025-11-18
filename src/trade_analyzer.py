"""
Enhanced trade probability analyzer with team context and advanced factors
"""
import numpy as np
from sklearn.preprocessing import MinMaxScaler

class TradeAnalyzer:
    def __init__(self, valuation_system):
        self.valuation = valuation_system
        
    def calculate_trade_probability(self, team1_players, team2_players):
        """
        Calculate probability of trade happening based on player values and context
        
        Args:
            team1_players: List of player names from team 1
            team2_players: List of player names from team 2
            
        Returns:
            Dictionary with probability and analysis
        """
        # Calculate total values for each side
        team1_value = sum([self.valuation.calculate_player_value(p) for p in team1_players])
        team2_value = sum([self.valuation.calculate_player_value(p) for p in team2_players])
        
        # Calculate value difference ratio
        if team1_value == 0 or team2_value == 0:
            return {
                'probability': 0,
                'team1_value': team1_value,
                'team2_value': team2_value,
                'value_difference': abs(team1_value - team2_value),
                'fairness_rating': 'Invalid',
                'recommendation': 'Trade cannot be evaluated - invalid players'
            }
        
        # Calculate fairness (closer to 1.0 = more fair)
        value_ratio = min(team1_value, team2_value) / max(team1_value, team2_value)
        
        # Base probability on fairness (increased max from 85 to 88)
        base_probability = value_ratio * 88
        
        # Adjust for value difference magnitude
        value_diff = abs(team1_value - team2_value)
        avg_value = (team1_value + team2_value) / 2
        diff_ratio = value_diff / avg_value if avg_value > 0 else 0
        
        # More nuanced penalty for imbalances
        if diff_ratio > 0.50:
            base_probability *= 0.65  # Major imbalance
        elif diff_ratio > 0.40:
            base_probability *= 0.75
        elif diff_ratio > 0.30:
            base_probability *= 0.82
        elif diff_ratio > 0.20:
            base_probability *= 0.90
        elif diff_ratio > 0.10:
            base_probability *= 0.96
        # No penalty if within 10%
        
        # Number of players factor (more complex trades less likely)
        total_players = len(team1_players) + len(team2_players)
        if total_players > 8:
            base_probability *= 0.85  # Very complex
        elif total_players > 6:
            base_probability *= 0.90
        elif total_players > 4:
            base_probability *= 0.95
        elif total_players == 2:
            base_probability *= 1.03  # Simple 1-for-1 trades easier
        
        # Get player details for context
        team1_details = [self.valuation.get_player_info(p) for p in team1_players]
        team2_details = [self.valuation.get_player_info(p) for p in team2_players]
        
        # Star player analysis
        team1_stars = [p for p in team1_details if p and p.get('Value', 0) > 100]
        team2_stars = [p for p in team2_details if p and p.get('Value', 0) > 100]
        team1_superstars = [p for p in team1_details if p and p.get('Value', 0) > 150]
        team2_superstars = [p for p in team2_details if p and p.get('Value', 0) > 150]
        
        # Star-for-star trades bonus
        if len(team1_stars) > 0 and len(team2_stars) > 0:
            if len(team1_superstars) > 0 and len(team2_superstars) > 0:
                base_probability *= 1.08  # Superstar swap
            else:
                base_probability *= 1.05  # Star swap
        
        # Age analysis (trading youth for veterans or vice versa)
        team1_avg_age = np.mean([p['Age'] for p in team1_details if p])
        team2_avg_age = np.mean([p['Age'] for p in team2_details if p])
        age_diff = abs(team1_avg_age - team2_avg_age)
        
        # Rebuilding vs contending indicator
        if age_diff > 5:
            # Likely rebuild/contender swap (young for vets or vice versa)
            base_probability *= 1.06  # Teams with different goals
        
        # Young prospect bonus (team trading for youth)
        team1_young = [p for p in team1_details if p and p.get('Age', 30) < 25]
        team2_young = [p for p in team2_details if p and p.get('Age', 30) < 25]
        
        if (len(team1_young) > 0 and team2_avg_age > 30) or \
           (len(team2_young) > 0 and team1_avg_age > 30):
            base_probability *= 1.04  # Youth for experience trade
        
        # Position balance check
        team1_positions = [p.get('Position', '') for p in team1_details if p]
        team2_positions = [p.get('Position', '') for p in team2_details if p]
        
        # Pitchers for batters or vice versa (positional need)
        team1_pitchers = sum(1 for p in team1_positions if 'P' in p or p == 'Pitcher')
        team2_pitchers = sum(1 for p in team2_positions if 'P' in p or p == 'Pitcher')
        team1_batters = len(team1_positions) - team1_pitchers
        team2_batters = len(team2_positions) - team2_pitchers
        
        if (team1_pitchers > 0 and team2_batters > 0) or \
           (team2_pitchers > 0 and team1_batters > 0):
            base_probability *= 1.03  # Addressing different needs
        
        # WAR efficiency check (high WAR players more tradeable)
        team1_wars = [p.get('WAR', 0) for p in team1_details if p]
        team2_wars = [p.get('WAR', 0) for p in team2_details if p]
        
        team1_has_elite = any(war > 5.0 for war in team1_wars)
        team2_has_elite = any(war > 5.0 for war in team2_wars)
        
        if team1_has_elite and team2_has_elite:
            base_probability *= 1.04  # Both getting proven talent
        
        # Rental/expiring contract simulation (simplified)
        # Players over 34 likely on short deals
        team1_rentals = sum(1 for p in team1_details if p and p.get('Age', 0) > 34)
        team2_rentals = sum(1 for p in team2_details if p and p.get('Age', 0) > 34)
        
        if team1_rentals > 0 or team2_rentals > 0:
            # Rental players easier to trade at deadline
            base_probability *= 1.02
        
        # Salary balance simulation (assume star players = big contracts)
        # Teams rarely take on huge salary without shedding some
        team1_expensive = sum(1 for p in team1_details if p and p.get('Value', 0) > 120)
        team2_expensive = sum(1 for p in team2_details if p and p.get('Value', 0) > 120)
        
        if team1_expensive > 0 and team2_expensive == 0:
            base_probability *= 0.93  # Salary dump concern
        elif team2_expensive > 0 and team1_expensive == 0:
            base_probability *= 0.93
        
        # Realistic trade context: identical value = slightly lower probability
        # (Real GMs rarely agree on exact equal value)
        if 0.98 <= value_ratio <= 1.0:
            base_probability *= 0.97  # Suspicious if TOO perfect
        
        # Cap probability at realistic maximum
        final_probability = min(base_probability, 94)  # Increased from 92 to 94
        
        # Floor probability at minimum
        final_probability = max(final_probability, 1)
        
        # Determine fairness rating with more granular scale
        if value_ratio > 0.98:
            fairness = "Extremely Fair - Nearly Equal Value"
        elif value_ratio > 0.92:
            fairness = "Very Fair - Balanced Trade"
        elif value_ratio > 0.85:
            fairness = "Fair - Reasonable Deal"
        elif value_ratio > 0.75:
            fairness = "Slightly Unbalanced"
        elif value_ratio > 0.65:
            fairness = "Moderately Unbalanced"
        elif value_ratio > 0.50:
            fairness = "Significantly Unbalanced"
        else:
            fairness = "Heavily Unbalanced - Lopsided Deal"
        
        # Generate detailed recommendation
        if final_probability > 80:
            recommendation = "✅ High likelihood - Excellent value match with strong trade logic"
        elif final_probability > 70:
            recommendation = "✅ Good likelihood - Fair deal that addresses team needs"
        elif final_probability > 60:
            recommendation = "⚠️ Moderate likelihood - Reasonably fair but some concerns"
        elif final_probability > 50:
            recommendation = "⚠️ Low-moderate likelihood - Noticeable value gap"
        elif final_probability > 35:
            recommendation = "❌ Low likelihood - Significant imbalance"
        elif final_probability > 20:
            recommendation = "❌ Very unlikely - Major value disparity"
        else:
            recommendation = "❌ Extremely unlikely - Heavily lopsided trade"
        
        # Add context-specific insights
        insights = []
        
        if len(team1_stars) > 0 and len(team2_stars) > 0:
            insights.append("Star-for-star trade increases feasibility")
        
        if age_diff > 5:
            insights.append("Age gap suggests rebuild/contend swap")
        
        if diff_ratio < 0.10:
            insights.append("Values nearly identical - very fair")
        
        if total_players > 6:
            insights.append("Complex multi-player deal may be harder to execute")
        
        if team1_pitchers > 0 and team2_batters > 0:
            insights.append("Trading pitching for hitting addresses positional needs")
        elif team2_pitchers > 0 and team1_batters > 0:
            insights.append("Trading hitting for pitching addresses positional needs")
        
        return {
            'probability': round(final_probability, 2),
            'team1_value': round(team1_value, 2),
            'team2_value': round(team2_value, 2),
            'value_difference': round(value_diff, 2),
            'value_ratio': round(value_ratio, 3),
            'fairness_rating': fairness,
            'recommendation': recommendation,
            'insights': insights,
            'team1_avg_age': round(team1_avg_age, 1),
            'team2_avg_age': round(team2_avg_age, 1),
            'total_players': total_players
        }
    
    def get_trade_details(self, team1_players, team2_players):
        """Get detailed breakdown of trade"""
        details = {
            'team1': [],
            'team2': []
        }
        
        for player in team1_players:
            info = self.valuation.get_player_info(player)
            if info:
                details['team1'].append(info)
        
        for player in team2_players:
            info = self.valuation.get_player_info(player)
            if info:
                details['team2'].append(info)
        
        return details
    
    def suggest_balancing_players(self, team1_players, team2_players, target_team):
        """Suggest players to add to balance trade"""
        result = self.calculate_trade_probability(team1_players, team2_players)
        
        team1_value = result['team1_value']
        team2_value = result['team2_value']
        
        value_diff = abs(team1_value - team2_value)
        
        if value_diff < 15:
            return "Trade is already well balanced!"
        
        # Determine which team needs to add value
        if team1_value < team2_value:
            deficit_team = 1
            deficit_value = value_diff
        else:
            deficit_team = 2
            deficit_value = value_diff
        
        # Get team abbreviation
        if deficit_team == 1:
            team_abbr = self.valuation.players_df[
                self.valuation.players_df['Name'].isin(team1_players)
            ].iloc[0]['Team']
        else:
            team_abbr = self.valuation.players_df[
                self.valuation.players_df['Name'].isin(team2_players)
            ].iloc[0]['Team']
        
        # Find suitable players from that team
        team_roster = self.valuation.get_team_players(team_abbr)
        
        suggestions = []
        for idx, player in team_roster.iterrows():
            if player['Name'] not in team1_players and player['Name'] not in team2_players:
                player_value = player.get('Value', 0)
                # Look for players within 40% of deficit value
                if abs(player_value - deficit_value) < deficit_value * 0.4:
                    suggestions.append({
                        'name': player['Name'],
                        'value': player_value,
                        'position': player['Position'],
                        'age': player['Age'],
                        'war': player.get('WAR', 0)
                    })
        
        # Sort by how close they are to the deficit value
        suggestions.sort(key=lambda x: abs(x['value'] - deficit_value))
        
        return suggestions[:7]  # Return top 7 suggestions
