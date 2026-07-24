"""Basic enqueue request construction example."""

from flywheel.models import EnqueueRequest


def main() -> None:
    req = EnqueueRequest(queue="default", payload={"n": 1}, delay_seconds=0.0)
    print(req.queue, req.payload)


if __name__ == "__main__":
    main()