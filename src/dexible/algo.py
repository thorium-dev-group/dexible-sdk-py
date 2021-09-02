from enum import Enum
from datetime import timedelta
import logging
import dexible.policy as policy
from .exceptions import DexibleAlgoException
from .common import Price

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
        slippages = list(
            filter(lambda p: p.name == policy.Slippage.tag, self.policies))
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
                return err

            if p.name in required:
                req_matches.append(p.name)

        if len(required) != len(req_matches):
            log.debug(f"Required and matches don't match. "
                      f"Required: {required}; Provided: {req_matches}")
            missing = list(
                filter(lambda req: req not in req_matches, required))
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

        if _type in [self.types.Limit, self.types.Limit.value]:
            return self.create_limit(*args, **kwargs)
        elif _type in [self.types.Market, self.types.Market.value]:
            return self.create_market(*args, **kwargs)
        elif _type in [self.types.StopLoss, self.types.StopLoss.value]:
            return self.create_stop_loss(*args, **kwargs)
        elif _type in [self.types.TWAP, self.types.TWAP.value]:
            return self.create_twap(*args, **kwargs)
        else:
            raise DexibleAlgoException(f"Unsupported algorithm type: {_type}")

    def create_limit(self, *args, **kwargs):
        # Invert price since quote are in output tokens while prices are
        # expressed in input tokens
        if "price" not in kwargs:
            raise DexibleAlgoException("price is required")
        price = kwargs.get("price")
        if type(price) != Price:
            raise DexibleAlgoException(
                "price must be of type dexible.common.Price")
        policies = self._build_base_polices(*args, **kwargs) + \
            [policy.LimitPrice(price=price)]

        return Limit(policies=policies, *args, **kwargs)

    def create_market(self, *args, **kwargs):
        return Market(policies=self._build_base_polices(*args, **kwargs),
                      *args, **kwargs)

    def create_stop_loss(self, *args, **kwargs):
        if "trigger_price" not in kwargs:
            raise DexibleAlgoException("trigger_price is required")
        trigger_price = kwargs.get("trigger_price")
        if type(trigger_price) != Price:
            raise DexibleAlgoException(
                "trigger_price must be of type dexible.common.Price")

        if "is_above" not in kwargs:
            raise DexibleAlgoException("is_above is required")
        is_above = kwargs.get("is_above")
        if type(is_above) != bool:
            raise DexibleAlgoException("is_above must be of type bool")

        policies = self._build_base_polices(*args, **kwargs) + \
            [policy.StopPrice(trigger=trigger_price,
                              above=is_above)]
        return StopLoss(policies=policies, *args, **kwargs)

    def create_twap(self, *args, **kwargs):
        if "time_window" not in kwargs:
            raise DexibleAlgoException("time_window is required")
        time_window = kwargs.get("time_window")
        if type(time_window) == dict:
            time_window = timedelta(**time_window)
        elif type(time_window) == timedelta:
            pass
        else:
            raise DexibleAlgoException(
                "time_window must be of type datetime.timedelta or dict")
        time_window_seconds = int(time_window.total_seconds())

        randomize_delay = kwargs.get("randomize_delay", False)
        if type(randomize_delay) != bool:
            raise DexibleAlgoException("randomize_delay must be of type bool")

        expire_after_time_window = kwargs.get(
            "expire_after_time_window", False)
        if type(expire_after_time_window) != bool:
            raise DexibleAlgoException(
                "expire_after_time_window must be of type bool")

        policies = self._build_base_polices(*args, **kwargs) + \
            [policy.BoundedDelay(
                randomize_delay=randomize_delay,
                time_window_seconds=time_window_seconds,
                expire_after_time_window=expire_after_time_window)]
        log.debug(f"Parsed TWAP duration in seconds: {time_window_seconds}")

        if "price_range" in kwargs:
            price_range = kwargs.get("price_range")
            if type(price_range) == dict:
                price_range = policy.PriceBounds(
                    base_price=price_range.get("base_price"),
                    lower_bound_percent=price_range.get("lower_bound_percent"),
                    upper_bound_percent=price_range.get("upper_bound_percent"))
            elif type(price_range) == policy.PriceBounds:
                pass
            else:
                raise DexibleAlgoException(
                    "price_range must be of type "
                    "dexible.policy.PriceBounds or dict")
            # invert price since quotes are in output tokens while prices are
            # expressed in input tokens
            policies.append(price_range)
        return TWAP(policies=policies, *args, **kwargs)

    def _build_base_polices(self, *args, **kwargs):
        if "gas_policy" not in kwargs:
            raise DexibleAlgoException("gas_policy is required")
        gas_policy = kwargs.get("gas_policy")
        if type(gas_policy) == dict:
            gas_policy = policy.GasCost(
                gas_type=gas_policy.get("type"),
                amount=gas_policy.get("amount"),
                deviation=gas_policy.get("deviation"))
        elif type(gas_policy) == policy.GasCost:
            pass
        else:
            raise DexibleAlgoException(
                "gas_policy must be of type dexible.policy.GasCost or dict")

        if "slippage_percent" not in kwargs:
            raise DexibleAlgoException("slippage_percent is required")
        slippage_percent = kwargs.get("slippage_percent")
        if type(slippage_percent) in [float, int]:
            slippage_percent = policy.Slippage(amount=slippage_percent)
        elif type(slippage_percent) == policy.Slippage:
            pass
        else:
            raise DexibleAlgoException(
                "slippage_percent must be of type "
                "dexible.policy.Slippage or float")

        policy_set = [gas_policy, slippage_percent]
        if "expiration" in kwargs:
            expiration = kwargs.get("expiration")
            if type(expiration) == int:
                expiration = policy.Expiration(seconds=expiration)
            elif type(expiration) == policy.Expiration:
                pass
            else:
                raise DexibleAlgoException(
                    "expiration must be of type "
                    "dexible.policy.Expiration of int")
            policy_set.append(expiration)

        return policy_set

types = AlgoWrapper.types