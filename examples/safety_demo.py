from flywheel.pause import PauseGate
from flywheel.quarantine import Quarantine


def main() -> None:
    gate = PauseGate()
    q = Quarantine()
    q.add("j-bad")
    print(gate.allow_claim(), q.blocked("j-bad"))


if __name__ == "__main__":
    main()