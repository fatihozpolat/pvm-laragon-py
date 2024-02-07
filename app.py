import PVM
import sys


def main():
    manager = PVM.PVM(sys.argv[1:])
    manager.run()


if __name__ == "__main__":
    main()
