from utils.patterns.strategy import Strategy

class BlacklistStrategy(Strategy):
    def apply(self, predicate: bool) -> bool:
        return not predicate