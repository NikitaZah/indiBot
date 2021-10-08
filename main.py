from strategies.slingshot_strategy import slingshot_strategy
from strategies.triple_strategy import triple_strategy, test_triple_strategy


def main():
    slingshot_strategy(restore=True, trading_allowed=True)


if __name__ == '__main__':
    main()
