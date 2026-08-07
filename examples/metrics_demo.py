from flywheel.metrics import Metrics

def main():
    m = Metrics()
    m.incr('enqueue')
    print(m.snapshot())

if __name__ == '__main__':
    main()

