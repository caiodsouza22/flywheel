"""Named registry for reusable allocation policies."""

from __future__ import annotations

from threading import RLock

from allot.errors import AllotError
from allot.policies import BurstPolicy, Policy, StrictPolicy, WeightedFairPolicy
from allot.overdraft import OverdraftPolicy


class UnknownPolicy(AllotError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"unknown policy: {name}")


class PolicyRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._lock = RLock()
        self.register("strict", StrictPolicy())
        self.register("burst", BurstPolicy())
        self.register("weighted_fair", WeightedFairPolicy())
        self.register("overdraft", OverdraftPolicy(overdraft=1.0))

    def register(self, name: str, policy: Policy) -> None:
        if not name:
            raise ValueError("policy name must be non-empty")
        with self._lock:
            self._policies[name] = policy

    def get(self, name: str) -> Policy:
        with self._lock:
            try:
                return self._policies[name]
            except KeyError as exc:
                raise UnknownPolicy(name) from exc

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._policies)
