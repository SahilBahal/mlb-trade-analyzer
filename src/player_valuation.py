"""
Enhanced player valuation system with advanced factors
"""
import pandas as pd
import numpy as np

class PlayerValuation:
    def __init__(self, players_df):
        self.players_df = players_df
        self.value_scores = {}
        
        # Positional scarcity multipliers (some positions harder to find)
        self.position_scarcity = {
            'C': 1.15,      # Catchers are scarce
            'SS': 1.10,     # Shortstops premium
            'CF': 1.08,     # Center fielders
            'SP': 1.05,     # Starting pitchers
            '3B': 1.03,
            '2B': 1.02,
            'OF': 1.00,
            '1B': 0.98,     # First base less scarce
            'DH': 0.95,     # DH easiest to fill
            'RP': 0.90,     # Relief pitchers
            'Pitcher': 1.05,
            'Batter': 1.00
        }
        
    def calculate_player_value(self, player_name):
        """Calculate comprehensive value score for a player"""
        player = self.players_df[self.players_df['Name'] == player_name]
        
        if player.empty:
            return 0
        
        player = player.iloc[0]
        
        if player['PlayerType'] == 'Batter':
            return self._calculate_batter_value(player)
        else:
            return self._calculate_pitcher_value(player)
    
    def _calculate_batter_value(self, player):
        """Calculate value for position players with enhanced factors"""
        # Base value from WAR (increased importance)
        war = float(player.get('WAR', 0))
        war_value = war * 18  # Increased from 15 to 18
        
        # Age adjustment with more granular curve
        age = float(player.get('Age', 30))
        if age < 23:
            age_multiplier = 1.35  # Young prospects
        elif age < 25:
            age_multiplier = 1.30
        elif age < 27:
            age_multiplier = 1.25  # Pre-prime
        elif age < 29:
            age_multiplier = 1.20  # Prime years
        elif age < 31:
            age_multiplier = 1.10  # Peak
        elif age < 33:
            age_multiplier = 1.00
        elif age < 35:
            age_multiplier = 0.85
        elif age < 37:
            age_multiplier = 0.70
        else:
            age_multiplier = 0.55  # Twilight
        
        # Performance metrics with adjusted weights
        avg = float(player.get('AVG', 0))
        obp = float(player.get('OBP', 0))
        slg = float(player.get('SLG', 0))
        hr = float(player.get('HR', 0))
        rbi = float(player.get('RBI', 0))
        
        # OPS+ calculation (weighted more heavily)
        ops = obp + slg
        performance_value = ops * 60 + hr * 0.6 + (rbi * 0.15)  # Increased weights
        
        # Games played (durability factor with penalty for injury concerns)
        games = float(player.get('Games', 0))
        if games >= 150:
            durability_factor = 1.25  # Iron man bonus
        elif games >= 140:
            durability_factor = 1.15
        elif games >= 120:
            durability_factor = 1.05
        elif games >= 100:
            durability_factor = 0.95
        elif games >= 80:
            durability_factor = 0.85  # Injury concern
        else:
            durability_factor = 0.70  # Major injury red flag
        
        # Positional scarcity bonus
        position = player.get('Position', 'Batter')
        position_multiplier = self.position_scarcity.get(position, 1.0)
        
        # Young star bonus (high WAR + young age)
        young_star_bonus = 1.0
        if war > 5.0 and age < 26:
            young_star_bonus = 1.20  # Future superstar
        elif war > 4.0 and age < 28:
            young_star_bonus = 1.10
        
        # MVP-caliber player bonus
        mvp_bonus = 1.0
        if war > 7.0:
            mvp_bonus = 1.25  # MVP-level player
        elif war > 6.0:
            mvp_bonus = 1.15  # All-Star level
        elif war > 5.0:
            mvp_bonus = 1.08
        
        # Power hitter bonus (30+ HR)
        power_bonus = 1.0
        if hr >= 40:
            power_bonus = 1.15
        elif hr >= 30:
            power_bonus = 1.08
        
        # Elite OBP bonus (walk machine)
        obp_bonus = 1.0
        if obp >= 0.400:
            obp_bonus = 1.12
        elif obp >= 0.380:
            obp_bonus = 1.06
        
        # Calculate total value with all factors
        base_value = (war_value + performance_value) * age_multiplier
        total_value = (base_value * durability_factor * position_multiplier * 
                      young_star_bonus * mvp_bonus * power_bonus * obp_bonus)
        
        return max(total_value, 1)  # Minimum value of 1
    
    def _calculate_pitcher_value(self, player):
        """Calculate value for pitchers with enhanced factors"""
        # Base value from WAR (increased importance)
        war = float(player.get('WAR', 0))
        war_value = war * 18  # Increased from 15
        
        # Age adjustment (pitchers age curve different)
        age = float(player.get('Age', 30))
        if age < 24:
            age_multiplier = 1.30  # Young arm
        elif age < 26:
            age_multiplier = 1.25
        elif age < 28:
            age_multiplier = 1.20  # Prime
        elif age < 30:
            age_multiplier = 1.15
        elif age < 32:
            age_multiplier = 1.05
        elif age < 34:
            age_multiplier = 0.90
        elif age < 36:
            age_multiplier = 0.75
        else:
            age_multiplier = 0.60  # Aging pitcher
        
        # Performance metrics with adjusted weights
        era = float(player.get('ERA', 5.0))
        whip = float(player.get('WHIP', 1.5))
        so = float(player.get('SO', 0))
        ip = float(player.get('IP', 0))
        games = float(player.get('Games', 0))
        
        # ERA+ calculation (lower is better, adjusted weights)
        era_value = max(0, (5.5 - era) * 25)  # Increased from 20
        whip_value = max(0, (2.2 - whip) * 35)  # Increased from 30
        so_value = so * 0.12  # Increased from 0.1
        
        performance_value = era_value + whip_value + so_value
        
        # Innings pitched (workload/durability)
        if ip >= 200:
            durability_factor = 1.30  # Workhorse
        elif ip >= 180:
            durability_factor = 1.20
        elif ip >= 160:
            durability_factor = 1.10
        elif ip >= 140:
            durability_factor = 1.00
        elif ip >= 120:
            durability_factor = 0.90
        elif ip >= 100:
            durability_factor = 0.80  # Injury concern
        else:
            durability_factor = 0.65  # Major injury flag
        
        # Starter vs reliever distinction
        starter_bonus = 1.0
        if games <= 35 and ip >= 140:  # Likely starter
            starter_bonus = 1.20  # Starters more valuable
        elif games > 50:  # Likely reliever
            starter_bonus = 0.85
        
        # Strikeout pitcher bonus (9+ K/9)
        k_per_9 = (so / ip * 9) if ip > 0 else 0
        strikeout_bonus = 1.0
        if k_per_9 >= 11.0:
            strikeout_bonus = 1.15  # Elite K rate
        elif k_per_9 >= 10.0:
            strikeout_bonus = 1.10
        elif k_per_9 >= 9.0:
            strikeout_bonus = 1.05
        
        # Ace bonus (elite ERA + high IP)
        ace_bonus = 1.0
        if era < 2.50 and ip >= 180:
            ace_bonus = 1.30  # True ace
        elif era < 3.00 and ip >= 170:
            ace_bonus = 1.20
        elif era < 3.30 and ip >= 160:
            ace_bonus = 1.10
        
        # Control bonus (low WHIP)
        control_bonus = 1.0
        if whip < 1.00:
            control_bonus = 1.15  # Elite control
        elif whip < 1.10:
            control_bonus = 1.08
        
        # Cy Young level bonus
        cy_young_bonus = 1.0
        if war > 6.5:
            cy_young_bonus = 1.25  # Cy Young candidate
        elif war > 5.5:
            cy_young_bonus = 1.15
        elif war > 4.5:
            cy_young_bonus = 1.08
        
        # Calculate total value with all factors
        base_value = (war_value + performance_value) * age_multiplier
        total_value = (base_value * durability_factor * starter_bonus * 
                      strikeout_bonus * ace_bonus * control_bonus * cy_young_bonus)
        
        return max(total_value, 1)
    
    def calculate_all_values(self):
        """Calculate values for all players"""
        print("Calculating enhanced player values with advanced metrics...")
        
        for idx, player in self.players_df.iterrows():
            player_name = player['Name']
            value = self.calculate_player_value(player_name)
            self.value_scores[player_name] = value
        
        # Add value column to dataframe
        self.players_df['Value'] = self.players_df['Name'].map(self.value_scores)
        
        print(f"✓ Calculated values for {len(self.value_scores)} players")
        print(f"✓ Top 5 most valuable players:")
        top_5 = self.players_df.nlargest(5, 'Value')[['Name', 'Team', 'Value', 'WAR']]
        for idx, player in top_5.iterrows():
            print(f"  {player['Name']:25} ({player['Team']}) - Value: {player['Value']:.2f}, WAR: {player['WAR']:.1f}")
        
        return self.value_scores
    
    def get_player_info(self, player_name):
        """Get detailed player information"""
        player = self.players_df[self.players_df['Name'] == player_name]
        
        if player.empty:
            return None
        
        player = player.iloc[0]
        value = self.value_scores.get(player_name, 0)
        
        info = {
            'Name': player['Name'],
            'Team': player['Team'],
            'Position': player['Position'],
            'Age': player['Age'],
            'PlayerType': player['PlayerType'],
            'Value': value
        }
        
        if player['PlayerType'] == 'Batter':
            info.update({
                'AVG': player.get('AVG', 0),
                'HR': player.get('HR', 0),
                'RBI': player.get('RBI', 0),
                'WAR': player.get('WAR', 0)
            })
        else:
            info.update({
                'ERA': player.get('ERA', 0),
                'WHIP': player.get('WHIP', 0),
                'SO': player.get('SO', 0),
                'WAR': player.get('WAR', 0)
            })
        
        return info
    
    def get_team_players(self, team_abbr):
        """Get all players from a specific team"""
        team_players = self.players_df[self.players_df['Team'] == team_abbr]
        return team_players.sort_values('Value', ascending=False) if 'Value' in team_players.columns else team_players
