"""
Main entry point for MLB Trade Analyzer
"""
import os
import sys
import pandas as pd
from colorama import Fore, Style, init

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_collector import MLBDataCollector
from player_valuation import PlayerValuation
from trade_analyzer import TradeAnalyzer
from ui import TradeUI

init(autoreset=True)

def initialize_data():
    """Initialize or load player data"""
    data_file = 'data/players_2025.csv'
    
    print(Fore.CYAN + "Initializing MLB Trade Analyzer...")
    print(Fore.CYAN + "=" * 50)
    
    # Check if data already exists
    if os.path.exists(data_file):
        print(Fore.YELLOW + "\nFound existing player data.")
        choice = input(Fore.GREEN + "Do you want to reload data from MLB? (y/n): ").strip().lower()
        
        if choice == 'y':
            collector = MLBDataCollector()
            players_df = collector.collect_all_players_2025()
            collector.save_data(players_df)
        else:
            print(Fore.CYAN + "Loading existing data...")
            players_df = pd.read_csv(data_file)
    else:
        print(Fore.YELLOW + "\nNo existing data found. Collecting player data...")
        collector = MLBDataCollector()
        players_df = collector.collect_all_players_2025()
        collector.save_data(players_df)
    
    print(Fore.GREEN + f"\n✓ Loaded {len(players_df)} players")
    print(Fore.GREEN + f"✓ Teams represented: {players_df['Team'].nunique()}")
    
    return players_df

def main():
    """Main application function"""
    try:
        # Initialize data
        players_df = initialize_data()
        
        # Initialize valuation system
        print(Fore.CYAN + "\nInitializing player valuation system...")
        valuation = PlayerValuation(players_df)
        valuation.calculate_all_values()
        print(Fore.GREEN + "✓ Player values calculated")
        
        # Initialize trade analyzer
        analyzer = TradeAnalyzer(valuation)
        
        # Initialize UI
        ui = TradeUI(analyzer, valuation)
        
        # Run application
        print(Fore.GREEN + "\n✓ System ready!")
        input(Fore.YELLOW + "\nPress Enter to start...")
        
        ui.run()
        
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\nApplication terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(Fore.RED + f"\nError: {str(e)}")
        print(Fore.YELLOW + "Please check your installation and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()