"""Prepaid credit balances that can be spent independently of quotas."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from allot.errors import AllotError


class InsufficientCredits(AllotError):
    def __init__(self, account_id: str, requested: float, balance: float) -> None:
        self.account_id = account_id
        self.requested = requested
        self.balance = balance
        super().__init__(
            f"insufficient credits for account={account_id}: "
            f"requested={requested} balance={balance}"
        )


@dataclass
class CreditAccount:
    id: str
    balance: float = 0.0
    currency: str = "credit"

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("account id must be non-empty")
        if self.balance < 0:
            raise ValueError("balance cannot be negative")


@dataclass
class CreditLedger:
    """Simple prepaid wallet ledger."""

    _accounts: dict[str, CreditAccount] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)

    def open(self, account_id: str, *, balance: float = 0.0, currency: str = "credit") -> CreditAccount:
        with self._lock:
            if account_id in self._accounts:
                raise AllotError(f"credit account already exists: {account_id}")
            account = CreditAccount(id=account_id, balance=balance, currency=currency)
            self._accounts[account_id] = account
            return account

    def get(self, account_id: str) -> CreditAccount:
        with self._lock:
            try:
                return self._accounts[account_id]
            except KeyError as exc:
                raise AllotError(f"unknown credit account: {account_id}") from exc

    def deposit(self, account_id: str, amount: float) -> float:
        if amount <= 0:
            raise ValueError("deposit amount must be positive")
        with self._lock:
            account = self.get(account_id)
            account.balance += amount
            return account.balance

    def charge(self, account_id: str, amount: float) -> float:
        if amount <= 0:
            raise ValueError("charge amount must be positive")
        with self._lock:
            account = self.get(account_id)
            if account.balance < amount:
                raise InsufficientCredits(account_id, amount, account.balance)
            account.balance -= amount
            return account.balance

    def transfer(self, src: str, dst: str, amount: float) -> None:
        if amount <= 0:
            raise ValueError("transfer amount must be positive")
        with self._lock:
            self.charge(src, amount)
            self.deposit(dst, amount)

    def balances(self) -> dict[str, float]:
        with self._lock:
            return {account_id: account.balance for account_id, account in sorted(self._accounts.items())}
