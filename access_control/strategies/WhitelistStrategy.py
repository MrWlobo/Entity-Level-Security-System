from els.utils.patterns.strategy import Strategy

class WhitelistStrategy(Strategy):
    def apply(self, predicate: bool) -> bool:
        return predicate