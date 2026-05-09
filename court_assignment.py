from typing import List
import random
from player import Player

class Player:
    def __init__(
        self,
        player_id: int,
        first_name: str,
        rating: float,
        matches_played: int,
    ):
        self.player_id = player_id
        self.first_name = first_name
        self.rating = rating
        self.matches_played = matches_played

    def __repr__(self):
        return f"{self.first_name} ({self.rating:.2f})"

def sort_players_for_straight(players: List[Player]) -> List[Player]:
    # Group players by (rating, matches_played)
    grouped = {}
    for p in players:
        key = (p.rating, p.matches_played)
        grouped.setdefault(key, []).append(p)

    # Shuffle inside each tied group
    for group in grouped.values():
        random.shuffle(group)

    # Sort groups by rating desc, matches desc
    sorted_keys = sorted(
        grouped.keys(),
        key=lambda k: (-k[0], -k[1])
    )

    # Flatten back into list
    sorted_players = []
    for key in sorted_keys:
        sorted_players.extend(grouped[key])

    return sorted_players

def assign_partners(court_players: List[Player]):
    """
    court_players must be length 4 and already ordered strongest → weakest
    """
    return [
        (court_players[0], court_players[3]),
        (court_players[1], court_players[2]),
    ]

def generate_straight_courts(players: List[Player], num_courts: int):
    expected_players = num_courts * 4
    if len(players) != expected_players:
        raise ValueError(f"Expected {expected_players} players")

    ordered = sort_players_for_straight(players)

    courts = []

    for i in range(num_courts):
        court_players = ordered[i * 4:(i + 1) * 4]
        teams = assign_partners(court_players)
        courts.append(teams)

    return courts

def generate_random_courts(players: List[Player], num_courts: int):
    expected_players = num_courts * 4
    if len(players) != expected_players:
        raise ValueError(f"Expected {expected_players} players")

    shuffled = players[:]
    random.shuffle(shuffled)

    courts = []

    for i in range(num_courts):
        court_players = shuffled[i * 4:(i + 1) * 4]
        teams = assign_partners(court_players)
        courts.append(teams)

    return courts

def generate_blended_courts(players: List[Player]):
    if len(players) != 12:
        raise ValueError("Blended mode requires exactly 12 players")

    ordered = sort_players_for_straight(players)

    blended_indices = [
        [0, 1, 4, 5],    # Court 1
        [2, 3, 6, 7],    # Court 2
        [8, 9, 10, 11],  # Court 3
    ]

    courts = []

    for indices in blended_indices:
        court_players = [ordered[i] for i in indices]
        teams = assign_partners(court_players)
        courts.append(teams)

    return courts


def generate_courts(players: List[Player], mode: str, num_courts: int):
    mode = mode.lower()

    if mode == "straight":
        return generate_straight_courts(players, num_courts)

    if mode == "random":
        return generate_random_courts(players, num_courts)

    if mode == "blended":
        if num_courts != 3:
            raise ValueError("Blended mode supports exactly 3 courts")
        return generate_blended_courts(players)

    raise ValueError(f"Unknown mode: {mode}")


def swap_players(courts, player_id_1: int, player_id_2: int):
    if player_id_1 == player_id_2:
        raise ValueError("Cannot swap the same player")

    pos1 = None
    pos2 = None

    # Locate both players
    for court_idx, court in enumerate(courts):
        for team_idx, team in enumerate(court):
            for player_idx, player in enumerate(team):
                if player.player_id == player_id_1:
                    pos1 = (court_idx, team_idx, player_idx)
                if player.player_id == player_id_2:
                    pos2 = (court_idx, team_idx, player_idx)

    if pos1 is None or pos2 is None:
        raise ValueError("One or both players not found in courts")

    c1, t1, p1 = pos1
    c2, t2, p2 = pos2

    # Convert tuples → lists to allow mutation
    team1 = list(courts[c1][t1])
    team2 = list(courts[c2][t2])

    # Swap
    team1[p1], team2[p2] = team2[p2], team1[p1]

    # Write back as tuples
    courts[c1][t1] = tuple(team1)
    courts[c2][t2] = tuple(team2)

    return courts

def courts_to_json(courts):
    """
    Convert court assignment structure to JSON-serializable dict.
    """
    json_output = {"courts": []}

    for court_idx, court in enumerate(courts, start=1):
        court_entry = {
            "court_number": court_idx,
            "teams": []
        }

        for team_idx, team in enumerate(court, start=1):
            team_entry = {
                "team_number": team_idx,
                "players": []
            }

            for player in team:
                team_entry["players"].append({
                    "player_id": player.player_id,
                    "first_name": player.first_name,
                    "rating": round(player.rating, 2),
                })

            court_entry["teams"].append(team_entry)

        json_output["courts"].append(court_entry)

    return json_output
