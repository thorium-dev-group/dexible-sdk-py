from enum import Enum
from datetime import timedelta
import logging
import dexible.policy as policy
from .exceptions import DexibleAlgoException

log = logging.getLogger('DexAlgo')

class DexibleBaseAlgorithm:
    name = None
    policies = None
    max_rounds = 0

    def __init__(self, policies, name, max_rounds=0, *args, **kwargs):
        self.policies = policies
        self.name = name
        self.max_rounds = max_rounds

    def verify(self):
        return self.verify_policies([])

    def serialize(self):
        return {"algorithm": self.name,
                "policies": [p.serialize() for p in self.policies]}

    def get_slippage(self):
        slippages = list(filter(lambda p: p.name == policy.Slippage.tag, self.policies))
        if len(slippages) == 0:
            return 0
        else:
            return slippages[0].amount

    def verify_policies(self, required=[]):
        # Must have at least Gas Cost and Slippage
        has_gas = False
        has_slippage = False
        # Must not have duplicate policies
        dup_check = []

        req_matches = []
        log.debug(f"Verifying policies: {self.name}")
        for p in self.policies:
            log.debug(f" Checking policy: {p.name}")
            if p.name in dup_check:
                return "Found duplicate policy definition: " + p.name
            dup_check.append(p.name)

            if p.name == policy.GasCost.tag:
                has_gas = True
            elif p.name == policy.Slippage.tag:
                has_slippage = True

            err = p.verify()
            if err is not None:
                log.error(f"Policy verification failed: {err}")

            if p.name in required:
                req_matches.append(p.name)

        if len(required) != len(req_matches):
            log.debug(f"Required and matches don't match. Required: {required}; Provided: {req_matches}")
            missing = list(filter(lambda req: req not in req_matches, required))
            return f"Must have following policies: {missing}"

        if has_gas and has_slippage:
            log.debug("All policies verified")
            return None

        return "Must have at least GasCost and Slippage policies"


    def __str__(self):
        return f"<Algo {self.name} policies: {self.policies}>"
    __repr__ = __str__

class Limit(DexibleBaseAlgorithm):
    tag = "Limit"

    def __init__(self, *args, **kwargs):
        super(Limit, self).__init__(name=self.tag, *args, **kwargs)

    def verify(self):
        return self.verify_policies([policy.LimitPrice.tag])


class Market(DexibleBaseAlgorithm):
    tag = "Market"

    def __init__(self, *args, **kwargs):
        super(Market, self).__init__(name=self.tag, *args, **kwargs)


class StopLoss(DexibleBaseAlgorithm):
    tag = "StopLoss"

    def __init__(self, *args, **kwargs):
        super(StopLoss, self).__init__(name=self.tag, *args, **kwargs)

    def verify(self):
        return self.verify_policies([policy.StopPrice.tag])


class TWAP(DexibleBaseAlgorithm):
    tag = "TWAP"

    def __init__(self, *args, **kwargs):
        super(TWAP, self).__init__(name=self.tag, *args, **kwargs)

    def verify(self):
        return self.verify_policies([policy.BoundedDelay.tag])


class AlgoWrapper:
    class types(Enum):
        Market = Market.tag
        Limit = Limit.tag
        StopLoss = StopLoss.tag
        TWAP = TWAP.tag

    def __init__(self):
        super(AlgoWrapper, self).__init__()

    def create(self, *args, **kwargs):
        _type = kwargs["type"]

        if _type == self.types.Limit.value:
            return self.create_limit(*args, **kwargs)
        elif _type == self.types.Market.value:
            return self.create_market(*args, **kwargs)
        elif _type == self.types.StopLoss.value:
            return self.create_stop_loss(*args, **kwargs)
        elif _type == self.types.TWAP.value:
            return self.create_twap(*args, **kwargs)
        else:
            raise DexibleAlgoException(f"Unsupported algorithm type: {_type}")

    def create_limit(self, *args, **kwargs):
        # Invert price since quote are in output tokens while prices are
        # expressed in input tokens
        policies = self._build_base_polices(*args, **kwargs) + \
                   [policy.LimitPrice(price=kwargs["price"])]

        return Limit(policies=policies, *args, **kwargs)

    def create_market(self, *args, **kwargs):
        return Market(policies=self._build_base_polices(*args, **kwargs), *args, **kwargs)

    def create_stop_loss(self, *args, **kwargs):
        policies = self._build_base_polices(*args, **kwargs) + \
                   [policy.StopPrice(trigger=kwargs.get("trigger_price"),
                                     above=kwargs.get("is_above"))]
        return StopLoss(policies=policies, *args, **kwargs)

    def create_twap(self, *args, **kwargs):
        time_window_seconds = int(timedelta(**kwargs["time_window"]).total_seconds())
        policies = self._build_base_polices(*args, **kwargs) + \
                   [policy.BoundedDelay(randomize_delay=kwargs.get("randomize_delay", False),
                                        time_window_seconds=time_window_seconds)]
        log.debug(f"Parsed TWAP duration in seconds: {time_window_seconds}")
        if "price_range" in kwargs:
            # invert price since quotes are in output tokens while prices are 
            # expressed in input tokens
            policies.append(policy.PriceBounds(
                base_price=kwargs["price_range"]["base_price"],
                lower_bound_percent=kwargs["price_range"]["lower_bound_percent"],
                upper_bound_percent=kwargs["price_range"]["upper_bound_percent"]))
        return TWAP(policies=policies, *args, **kwargs)

    def _build_base_polices(self, *args, **kwargs):
        return [policy.GasCost(gas_type=kwargs.get("gas_policy").get("type"),
                               amount=kwargs.get("gas_policy").get("amount"),
                               deviation=kwargs.get("gas_policy").get("deviation")),
                policy.Slippage(amount=kwargs["slippage_percent"])]

