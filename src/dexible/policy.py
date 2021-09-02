from enum import Enum


class DexibleBasePolicy:
    name = None

    def __init__(self, name):
        self.name = name

    def serialize(self):
        raise Exception("Must implement serialize function")

    def verify(self):
        raise Exception("Must implement verify function")


class BoundedDelay(DexibleBasePolicy):
    tag = "BoundedDelay"

    def __init__(self, time_window_seconds, randomize_delay,
                 expire_after_time_window=None):
        super(BoundedDelay, self).__init__(self.tag)
        self.time_window_seconds = time_window_seconds
        self.randomize_delay = randomize_delay
        self.expire_after_time_window = expire_after_time_window

    def verify(self):
        return None

    def serialize(self):
        return {"type": self.name,
                "params": {
                    "timeWindow": self.time_window_seconds,
                    "randomize": self.randomize_delay,
                    "expireAfterTimeWindow": self.expire_after_time_window}}

    def __str__(self):
        return f"<Policy {self.tag} " \
            f"time_window_seconds: {self.time_window_seconds}, " \
            f"randomize_delay: {self.randomize_delay}, " \
            f"expire_after_time_window: {self.expire_after_time_window}>"
    __repr__ = __str__


class Expiration(DexibleBasePolicy):
    tag = "Expiration"

    def __init__(self, seconds):
        super(Expiration, self).__init__(self.tag)
        self.seconds = seconds

    def verify(self):
        return None

    def serialize(self):
        return {"type": self.name,
                "params": {"seconds": self.seconds}}

    def __str__(self):
        return f"<Policy {self.tag} seconds: {self.seconds}>"
    __repr__ = __str__


class FailLimit(DexibleBasePolicy):
    tag = "FailLimit"

    def __init__(self, max_failures):
        super(FailLimit, self).__init__(self.tag)
        self.max_failures = max_failures

    def verify(self):
        return None

    def serialize(self):
        return {"type": self.name,
                "params": {"maxFailures": self.max_failures}}

    def __str__(self):
        return f"<Policy {self.tag} max_failures: {self.max_failures}>"
    __repr__ = __str__


class GasCost(DexibleBasePolicy):
    tag = "GasCost"

    def __init__(self, gas_type, amount=None, deviation=None):
        super(GasCost, self).__init__(self.tag)
        if Enum in type(gas_type).__mro__:
            gas_type = gas_type.value
        self.gas_type = gas_type
        self.amount = amount
        self.deviation = deviation

    def verify(self):
        if self.gas_type == "fixed":
            if self.amount is None:
                return "Fixed gas type requires an amount parameter"

    def serialize(self):
        return {"type": self.name,
                "params": {"gasType": self.gas_type,
                           "amount": self.amount or 0,
                           "deviation": self.deviation or 0}}

    def __str__(self):
        return f"<Policy {self.tag} " \
            f"gas_type: {self.gas_type}, " \
            f"amount: {self.amount}, "\
            f"deviation {self.deviation}>"
    __repr__ = __str__


class LimitPrice(DexibleBasePolicy):
    tag = "LimitPrice"
    price = None

    def __init__(self, price):
        super(LimitPrice, self).__init__(self.tag)
        self.price = price

    def verify(self):
        return None

    def serialize(self):
        return {"type": self.name,
                "params": {"price": self.price.toJSON()}}

    def __str__(self):
        return f"<Policy {self.tag} price: {self.price}>"
    __repr__ = __str__


class PriceBounds(DexibleBasePolicy):
    tag = "PriceBounds"

    def __init__(self, base_price,
                 upper_bound_percent=None, lower_bound_percent=None):
        super(PriceBounds, self).__init__(self.tag)
        self.base_price = base_price
        self.upper_bound_percent = upper_bound_percent
        self.lower_bound_percent = lower_bound_percent

    def verify(self):
        if self.upper_bound_percent is None and \
                self.lower_bound_percent is None:
            return "PriceBounds requires either an upper_bound_percent "\
                "or lower_bound_percent parameter or both"

    def serialize(self):
        return {"type": self.name,
                "params": {"basePrice": self.base_price.toJSON(),
                           "upperBoundPercentage": self.upper_bound_percent,
                           "lowerBoundPercentage": self.lower_bound_percent}}

    def __str__(self):
        return f"<Policy {self.tag} " \
            f"upper_bound_percent: {self.upper_bound_percent}, " \
            f"lower_bound_percent: {self.lower_bound_percent}>"
    __repr__ = __str__


class Slippage(DexibleBasePolicy):
    tag = "Slippage"

    def __init__(self, amount):
        super(Slippage, self).__init__(self.tag)
        self.amount = amount

    def verify(self):
        return None

    def serialize(self):
        return {"type": self.name,
                "params": {"amount": self.amount}}

    def __str__(self):
        return f"<Policy {self.tag} amount: {self.amount}>"
    __repr__ = __str__


class StopPrice(DexibleBasePolicy):
    tag = "StopPrice"

    def __init__(self, trigger, above):
        super(StopPrice, self).__init__(self.tag)
        self.trigger = trigger
        self.above = above

    def verify(self):
        return None

    def serialize(self):
        return {"type": self.name,
                "params": {"trigger": self.trigger.toJSON(),
                           "above": self.above}}

    def __str__(self):
        return f"<Policy {self.tag} trigger: {self.trigger}, " \
            f"above: {self.above}>"
    __repr__ = __str__
