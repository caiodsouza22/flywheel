"""allot — multi-tenant quota, budget, and rate allocation."""

from allot.audit import AuditEvent, AuditLog
from allot.clock import Clock, FrozenClock, SystemClock
from allot.engine import AllocationEngine
from allot.errors import (
    AllotError,
    InsufficientCapacity,
    InvalidWindow,
    QuotaExceeded,
    UnknownResource,
    UnknownTenant,
)
from allot.models import (
    AllocationDecision,
    AllocationRequest,
    Budget,
    DecisionKind,
    Quota,
    Resource,
    Softness,
    Tenant,
)
from allot.policies import BurstPolicy, StrictPolicy, WeightedFairPolicy
from allot.store import InMemoryStore, Store
from allot.windows import FixedWindow, SlidingWindow, WindowBounds

__all__ = [
    "AllocationDecision",
    "AllocationEngine",
    "AllocationRequest",
    "AllotError",
    "AuditEvent",
    "AuditLog",
    "Budget",
    "BurstPolicy",
    "Clock",
    "DecisionKind",
    "FixedWindow",
    "FrozenClock",
    "InMemoryStore",
    "InsufficientCapacity",
    "InvalidWindow",
    "Quota",
    "QuotaExceeded",
    "Resource",
    "SlidingWindow",
    "Softness",
    "Store",
    "StrictPolicy",
    "SystemClock",
    "Tenant",
    "UnknownResource",
    "UnknownTenant",
    "WeightedFairPolicy",
    "WindowBounds",
]

__version__ = "0.1.0"
