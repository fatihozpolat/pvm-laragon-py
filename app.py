import PvmManager

import sys


def main():
    manager = PvmManager.PvmManager(sys.argv[1:])
    manager.run()


if __name__ == "__main__":
    main()
