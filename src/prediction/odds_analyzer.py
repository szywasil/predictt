import pandas as pd
import config

def normalize_team_name_for_odds(team_name):
    team_name = team_name.replace(" FC", "").replace(" AFC", "")
    team_name = team_name.replace(" United", "")
    team_name = team_name.replace("& Hove Albion", "and Hove Albion")
    return team_name.strip()

class OddsAnalyzer:
    def __init__(self, value_threshold=None):
        self.value_threshold = value_threshold or getattr(config, 'VALUE_BET_THRESHOLD', 0.035)

    def odds_to_probability(self, odds):
        return 1 / odds if odds > 0 else 0

    def find_value_bets(self, predictions, odds_data):
        value_bets = []
        
        for pred in predictions:
            home_norm = normalize_team_name_for_odds(pred.get('home_team', ''))
            away_norm = normalize_team_name_for_odds(pred.get('away_team', ''))
            
            possible_keys = [
                f"{pred.get('home_team', '')} vs {pred.get('away_team', '')}",
                f"{home_norm} vs {away_norm}"
            ]
            
            odds = None
            for key in possible_keys:
                if key in odds_data:
                    odds = odds_data[key]
                    break
            
            if odds is None:
                continue
                
            match_display = f"{pred.get('home_team')} vs {pred.get('away_team')}"
            
            # Poprawione pobieranie prawdopodobieństw
            home_prob = pred.get("home_win_prob") or pred.get("probabilities", {}).get("home_win", 0)
            draw_prob = pred.get("draw_prob") or pred.get("probabilities", {}).get("draw", 0)
            away_prob = pred.get("away_win_prob") or pred.get("probabilities", {}).get("away_win", 0)
            
            outcomes = [
                ("home_win", "home", home_prob),
                ("draw", "draw", draw_prob),
                ("away_win", "away", away_prob)
            ]
            
            for outcome_name, odds_key, model_prob in outcomes:
                if odds_key not in odds or model_prob < 0.01:
                    continue
                    
                bookmaker_odds = odds[odds_key]
                bookmaker_prob = self.odds_to_probability(bookmaker_odds)
                edge = model_prob - bookmaker_prob
                
                if edge >= 0.035 and model_prob >= 0.52:
                    value_bet = {
                        "match": match_display,
                        "outcome": outcome_name.replace("_", " ").title(),
                        "model_probability": model_prob,
                        "bookmaker_odds": bookmaker_odds,
                        "edge": edge,
                        "confidence": pred.get("confidence", model_prob)
                    }
                    value_bets.append(value_bet)
        
        value_bets.sort(key=lambda x: x.get("edge", 0), reverse=True)
        return value_bets

    def display_value_bets(self, value_bets, top_n=15):
        if not value_bets:
            print("No value bets found.")
            return
        print(f"\nVALUE BETS FOUND: {len(value_bets)}")
        for i, bet in enumerate(value_bets[:top_n], 1):
            print(f"{i:2d}. {bet['match']} → {bet['outcome']} | Edge: +{bet['edge']:.1%} | Prob: {bet['model_probability']:.1%}")

    def to_dataframe(self, value_bets):
        return pd.DataFrame(value_bets)
