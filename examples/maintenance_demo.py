from flywheel.drain import Drain
from flywheel.pause import PauseGate


def main() -> None:
    gate = PauseGate()
    gate.close("rolling-restart")
    drain = Drain()
    print(gate.snapshot(), drain.snapshot())


if __name__ == "__main__":
    main()