"""allot — multi-tenant quota, budget, and rate allocation."""

from allot.audit import AuditEvent, AuditLog
from allot.clock import Clock, FrozenClock, SystemClock
from allot.config import AllotConfig, dump_config_dict, load_config_dict, load_config_file, parse_config
from allot.engine import AllocationEngine
from allot.errors import (
    AllotError,
    ConfigError,
    InsufficientCapacity,
    InsufficientSlidingBudget,
    InvalidWindow,
    LeaseConflict,
    LeaseError,
    LeaseExpired,
    LeaseNotFound,
    QuotaExceeded,
    ReservationError,
    ReservationExpired,
    ReservationNotFound,
    StaleFencingToken,
    UnknownResource,
    UnknownTenant,
)
from allot.fairness import FairQueue
from allot.leases import Lease, LeaseManager
from allot.metrics import MetricsRegistry
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
from allot.reconcile import ReconcileReport, UsageDrift, UsageExpectation, apply_corrections, reconcile_usage
from allot.reservations import Reservation, ReservationBook, ReservationState
from allot.sliding_budget import SlidingBudgetAccount, SlidingBudgetLedger, SpendEvent
from allot.store import InMemoryStore, Store
from allot.windows import FixedWindow, SlidingWindow, WindowBounds

__all__ = [
    "AllocationDecision",
    "AllocationEngine",
    "AllocationRequest",
    "AllotConfig",
    "AllotError",
    "AuditEvent",
    "AuditLog",
    "Budget",
    "BurstPolicy",
    "Clock",
    "ConfigError",
    "DecisionKind",
    "FairQueue",
    "FixedWindow",
    "FrozenClock",
    "InMemoryStore",
    "InsufficientCapacity",
    "InsufficientSlidingBudget",
    "InvalidWindow",
    "Lease",
    "LeaseConflict",
    "LeaseError",
    "LeaseExpired",
    "LeaseManager",
    "LeaseNotFound",
    "MetricsRegistry",
    "Quota",
    "QuotaExceeded",
    "ReconcileReport",
    "Reservation",
    "ReservationBook",
    "ReservationError",
    "ReservationExpired",
    "ReservationNotFound",
    "ReservationState",
    "Resource",
    "SlidingBudgetAccount",
    "SlidingBudgetLedger",
    "SlidingWindow",
    "Softness",
    "SpendEvent",
    "StaleFencingToken",
    "Store",
    "StrictPolicy",
    "SystemClock",
    "Tenant",
    "UnknownResource",
    "UnknownTenant",
    "UsageDrift",
    "UsageExpectation",
    "WeightedFairPolicy",
    "WindowBounds",
    "apply_corrections",
    "dump_config_dict",
    "load_config_dict",
    "load_config_file",
    "parse_config",
    "reconcile_usage",
]

__version__ = "0.1.0"
