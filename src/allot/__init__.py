"""allot — multi-tenant quota, budget, and rate allocation."""

from allot.audit import AuditEvent, AuditLog
from allot.batch import BatchAllocator, BatchResult
from allot.clock import Clock, FrozenClock, SystemClock
from allot.config import AllotConfig, dump_config_dict, load_config_dict, load_config_file, parse_config
from allot.credits import CreditAccount, CreditLedger, InsufficientCredits
from allot.engine import AllocationEngine
from allot.engine_ext import EngineFacade
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
from allot.hierarchy import TenantHierarchy
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
from allot.overdraft import OverdraftPolicy
from allot.policies import BurstPolicy, StrictPolicy, WeightedFairPolicy
from allot.rate_limit import LeakyBucket, RateLimited, TokenBucket
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
    "BatchAllocator",
    "BatchResult",
    "Budget",
    "BurstPolicy",
    "Clock",
    "ConfigError",
    "CreditAccount",
    "CreditLedger",
    "DecisionKind",
    "EngineFacade",
    "FairQueue",
    "FixedWindow",
    "FrozenClock",
    "InMemoryStore",
    "InsufficientCapacity",
    "InsufficientCredits",
    "InsufficientSlidingBudget",
    "InvalidWindow",
    "LeakyBucket",
    "Lease",
    "LeaseConflict",
    "LeaseError",
    "LeaseExpired",
    "LeaseManager",
    "LeaseNotFound",
    "MetricsRegistry",
    "OverdraftPolicy",
    "Quota",
    "QuotaExceeded",
    "RateLimited",
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
    "TenantHierarchy",
    "TokenBucket",
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
