from strategies.slingshot_strategy import slingshot_strategy
from strategies.triple_strategy import triple_strategy, test_triple_strategy
from strategies.net_strategy import net


def main():
    # net(1.3)
    slingshot_strategy(restore=True, trading_allowed=True)

if __name__ == '__main__':
    main()
