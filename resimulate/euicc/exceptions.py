class ESIMException(Exception):
    def __init__(self, sw: str):
        self.sw = sw

    def __str__(self):
        return f"Error: {self.sw}"
