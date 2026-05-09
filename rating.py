import math


def expected_game_share(rating_a: float, rating_b: float, scale: float = 0.5) -> float:
    delta_r = rating_a - rating_b
    return 1.0 / (1.0 + math.exp(-delta_r / scale))


def observed_game_share(games_a: int, games_b: int) -> float:
    total_games = games_a + games_b
    if total_games == 0:
        raise ValueError("Total games must be > 0")
    return games_a / total_games


def match_weight(total_games, reference_games=10, cap=1.3):
    return min(cap, total_games / reference_games)



def team_rating(player_ratings: list[float]) -> float:
    if len(player_ratings) == 0:
        raise ValueError("Team must have at least one player")
    return sum(player_ratings) / len(player_ratings)


def rating_update(
    team_a_ratings: list[float],
    team_b_ratings: list[float],
    games_a: int,
    games_b: int,
    k: float = 2,
    scale: float = 0.45,
    reference_games: int = 6, #gives less weight to shorter matches
) -> tuple[list[float], list[float]]:

    rating_a = team_rating(team_a_ratings)
    rating_b = team_rating(team_b_ratings)

    expected = expected_game_share(rating_a, rating_b, scale)
    observed = observed_game_share(games_a, games_b)

    delta = observed - expected
    weight = match_weight(games_a + games_b, reference_games)

    team_delta = k * delta * weight

    #per_player_a = team_delta / len(team_a_ratings)
    #per_player_b = -team_delta / len(team_b_ratings)
    per_player_a = team_delta
    per_player_b = -team_delta


    new_team_a = [r + per_player_a for r in team_a_ratings]
    new_team_b = [r + per_player_b for r in team_b_ratings]

    return new_team_a, new_team_b
