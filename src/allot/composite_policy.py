"""Compose multiple policies with first-non-deny or min-grant strategies."""

from __future__ import annotations

from dataclasses import dataclass

from allot.policies import Policy, PolicyContext, PolicyResult


@dataclass
class FirstAllowPolicy(Policy):
    """Try policies in order; return the first positive grant."""

    policies: tuple[Policy, ...]

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        last = PolicyResult(granted=0.0, reason="no_policies")
        for policy in self.policies:
            result = policy.decide(ctx)
            last = result
            if result.granted > 0:
                return result
        return last


@dataclass
class MinGrantPolicy(Policy):
    """Grant the minimum amount approved by every policy."""

    policies: tuple[Policy, ...]

    def decide(self, ctx: PolicyContext) -> PolicyResult:
        if not self.policies:
            return PolicyResult(granted=0.0, reason="no_policies")
        grants = [policy.decide(ctx) for policy in self.policies]
        granted = min(item.granted for item in grants)
        if granted <= 0:
            reason = next((item.reason for item in grants if item.granted <= 0), "denied")
            return PolicyResult(granted=0.0, reason=reason)
        return PolicyResult(granted=granted, reason="min_grant")
