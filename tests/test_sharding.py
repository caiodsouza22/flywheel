"""Tests for shard routing."""

from __future__ import annotations

from allot import AllocationRequest
from allot.sharding import Shard, ShardCapacityPlan, ShardRouter


def test_router_is_deterministic_and_splits_capacity() -> None:
    router = ShardRouter(
        [
            Shard(id="s1", weight=1),
            Shard(id="s2", weight=3),
        ]
    )
    request = AllocationRequest(tenant_id="acme", resource="api", amount=1)
    first = router.assign(request)
    second = router.assign(request)
    assert first.shard.id == second.shard.id
    plan = ShardCapacityPlan(router).split(100)
    assert abs(plan["s1"] + plan["s2"] - 100) < 1e-9
    assert plan["s2"] > plan["s1"]


def test_distribution_covers_keys() -> None:
    router = ShardRouter([Shard(id="a"), Shard(id="b")])
    counts = router.distribution([f"key-{i}" for i in range(50)])
    assert sum(counts.values()) == 50
    assert set(counts) == {"a", "b"}
