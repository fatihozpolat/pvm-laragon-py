import PVM
import sys


def main():
    # herhangi bir argüman almadan çalıştırıldığında hata verir
    if len(sys.argv) == 1:
        print("Usage: pvm [args]")
        sys.exit(1)

    manager = PVM.PVM(sys.argv[1:])
    manager.run()


if __name__ == "__main__":
    main()
