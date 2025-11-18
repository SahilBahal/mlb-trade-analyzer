"""
User interface for trade analyzer
"""
from colorama import Fore, Style, init
from tabulate import tabulate
import os

init(autoreset=True)

class TradeUI:
    def __init__(self, analyzer, valuation):
        self.analyzer = analyzer
        self.valuation = valuation
        self.players_df = valuation.players_df
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print application header"""
        print(Fore.CYAN + "=" * 70)
        print(Fore.CYAN + "              MLB TRADE PROBABILITY ANALYZER - 2025")
        print(Fore.CYAN + "=" * 70)
        print()
    
    def display_main_menu(self):
        """Display main menu"""
        print(Fore.YELLOW + "\nMAIN MENU:")
        print("1. Create New Trade Scenario")
        print("2. View All Teams")
        print("3. Search for Player")
        print("4. View Team Roster")
        print("5. Exit")
        print()
        
    def get_user_choice(self, prompt, valid_choices):
        """Get validated user input"""
        while True:
            choice = input(Fore.GREEN + prompt).strip()
            if choice in valid_choices:
                return choice
            print(Fore.RED + f"Invalid choice. Please select from {valid_choices}")
    
    def search_player(self):
        """Search for a player by name"""
        search_term = input(Fore.GREEN + "\nEnter player name (or part of name): ").strip()
        
        if not search_term:
            print(Fore.RED + "Search term cannot be empty!")
            return
        
        # Search for players
        matches = self.players_df[
            self.players_df['Name'].str.contains(search_term, case=False, na=False)
        ]
        
        if matches.empty:
            print(Fore.RED + f"No players found matching '{search_term}'")
            return
        
        print(Fore.CYAN + f"\nFound {len(matches)} player(s):")
        
        # Display matches
        display_data = []
        for idx, player in matches.iterrows():
            value = self.valuation.calculate_player_value(player['Name'])
            display_data.append([
                player['Name'],
                player['Team'],
                player['Position'],
                player['Age'],
                f"{value:.2f}"
            ])
        
        print(tabulate(display_data, 
                      headers=['Name', 'Team', 'Position', 'Age', 'Value'],
                      tablefmt='grid'))
    
    def view_all_teams(self):
        """Display all MLB teams"""
        teams = self.players_df['Team'].unique()
        teams = sorted([t for t in teams if isinstance(t, str)])
        
        print(Fore.CYAN + "\n30 MLB Teams:")
        print(Fore.CYAN + "=" * 50)
        
        # Display in columns
        for i in range(0, len(teams), 3):
            row_teams = teams[i:i+3]
            print("  ".join(f"{team:15}" for team in row_teams))
    
    def view_team_roster(self):
        """View roster for a specific team"""
        team = input(Fore.GREEN + "\nEnter team abbreviation (e.g., NYY, LAD): ").strip().upper()
        
        roster = self.valuation.get_team_players(team)
        
        if roster.empty:
            print(Fore.RED + f"No players found for team '{team}'")
            return
        
        print(Fore.CYAN + f"\n{team} Roster:")
        print(Fore.CYAN + "=" * 70)
        
        display_data = []
        for idx, player in roster.iterrows():
            value = player.get('Value', 0)
            war = player.get('WAR', 0)
            display_data.append([
                player['Name'],
                player['Position'],
                player['Age'],
                f"{war:.1f}",
                f"{value:.2f}"
            ])
        
        print(tabulate(display_data,
                      headers=['Name', 'Position', 'Age', 'WAR', 'Value'],
                      tablefmt='grid'))
    
    def select_players(self, team_name):
        """Interactive player selection"""
        print(Fore.YELLOW + f"\nSelect players for {team_name}:")
        print(Fore.YELLOW + "Enter player names one at a time. Type 'done' when finished.")
        
        selected_players = []
        
        while True:
            player_name = input(Fore.GREEN + f"Player {len(selected_players) + 1} (or 'done'): ").strip()
            
            if player_name.lower() == 'done':
                if not selected_players:
                    print(Fore.RED + "You must select at least one player!")
                    continue
                break
            
            # Check if player exists
            matches = self.players_df[
                self.players_df['Name'].str.contains(player_name, case=False, na=False)
            ]
            
            if matches.empty:
                print(Fore.RED + f"Player '{player_name}' not found. Try again.")
                continue
            
            if len(matches) > 1:
                print(Fore.YELLOW + f"\nMultiple players found. Please specify:")
                for idx, player in matches.iterrows():
                    print(f"  - {player['Name']} ({player['Team']}, {player['Position']})")
                continue
            
            exact_name = matches.iloc[0]['Name']
            
            if exact_name in selected_players:
                print(Fore.RED + "Player already selected!")
                continue
            
            selected_players.append(exact_name)
            print(Fore.GREEN + f"✓ Added {exact_name}")
        
        return selected_players
    
    def display_trade_analysis(self, team1_players, team2_players):
        """Display comprehensive trade analysis"""
        self.clear_screen()
        self.print_header()
        
        print(Fore.CYAN + "TRADE SCENARIO ANALYSIS")
        print(Fore.CYAN + "=" * 70)
        
        # Get trade details
        details = self.analyzer.get_trade_details(team1_players, team2_players)
        result = self.analyzer.calculate_trade_probability(team1_players, team2_players)
        
        # Display Team 1
        print(Fore.YELLOW + "\nTEAM 1 SENDS:")
        team1_data = []
        for player in details['team1']:
            if player['PlayerType'] == 'Batter':
                stats = f"AVG: {player['AVG']:.3f}, HR: {int(player['HR'])}, WAR: {player['WAR']:.1f}"
            else:
                stats = f"ERA: {player['ERA']:.2f}, SO: {int(player['SO'])}, WAR: {player['WAR']:.1f}"
            
            team1_data.append([
                player['Name'],
                player['Position'],
                player['Age'],
                stats,
                f"{player['Value']:.2f}"
            ])
        
        print(tabulate(team1_data,
                      headers=['Name', 'Position', 'Age', 'Stats', 'Value'],
                      tablefmt='grid'))
        print(Fore.CYAN + f"Total Team 1 Value: {result['team1_value']:.2f}")
        
        # Display Team 2
        print(Fore.YELLOW + "\nTEAM 2 SENDS:")
        team2_data = []
        for player in details['team2']:
            if player['PlayerType'] == 'Batter':
                stats = f"AVG: {player['AVG']:.3f}, HR: {int(player['HR'])}, WAR: {player['WAR']:.1f}"
            else:
                stats = f"ERA: {player['ERA']:.2f}, SO: {int(player['SO'])}, WAR: {player['WAR']:.1f}"
            
            team2_data.append([
                player['Name'],
                player['Position'],
                player['Age'],
                stats,
                f"{player['Value']:.2f}"
            ])
        
        print(tabulate(team2_data,
                      headers=['Name', 'Position', 'Age', 'Stats', 'Value'],
                      tablefmt='grid'))
        print(Fore.CYAN + f"Total Team 2 Value: {result['team2_value']:.2f}")
        
        # Display probability and analysis
        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.YELLOW + "\nTRADE PROBABILITY ANALYSIS:")
        print(Fore.CYAN + "=" * 70)
        
        # Color code probability
        prob = result['probability']
        if prob > 75:
            prob_color = Fore.GREEN
        elif prob > 50:
            prob_color = Fore.YELLOW
        else:
            prob_color = Fore.RED
        
        print(f"\n{prob_color}Trade Probability: {prob:.2f}%")
        print(Style.RESET_ALL + f"Fairness Rating: {result['fairness_rating']}")
        print(f"Value Difference: {result['value_difference']:.2f}")
        print(f"Value Ratio: {result['value_ratio']:.3f}")
        print(f"\nRecommendation: {result['recommendation']}")
        
        print(Fore.CYAN + "\n" + "=" * 70)
    
    def create_trade_scenario(self):
        """Main trade creation workflow"""
        self.clear_screen()
        self.print_header()
        
        print(Fore.CYAN + "CREATE NEW TRADE SCENARIO")
        print(Fore.CYAN + "=" * 70)
        
        # Select players for Team 1
        team1_players = self.select_players("Team 1")
        
        # Select players for Team 2
        team2_players = self.select_players("Team 2")
        
        # Display analysis
        self.display_trade_analysis(team1_players, team2_players)
        
        # Ask if user wants to save or modify
        print(Fore.YELLOW + "\nOptions:")
        print("1. Create another trade scenario")
        print("2. Return to main menu")
        
        choice = self.get_user_choice("Select option: ", ['1', '2'])
        
        if choice == '1':
            self.create_trade_scenario()
    
    def run(self):
        """Main application loop"""
        while True:
            self.clear_screen()
            self.print_header()
            self.display_main_menu()
            
            choice = self.get_user_choice("Select an option: ", ['1', '2', '3', '4', '5'])
            
            if choice == '1':
                self.create_trade_scenario()
            elif choice == '2':
                self.view_all_teams()
                input(Fore.GREEN + "\nPress Enter to continue...")
            elif choice == '3':
                self.search_player()
                input(Fore.GREEN + "\nPress Enter to continue...")
            elif choice == '4':
                self.view_team_roster()
                input(Fore.GREEN + "\nPress Enter to continue...")
            elif choice == '5':
                print(Fore.CYAN + "\nThank you for using MLB Trade Analyzer!")
                break
