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
