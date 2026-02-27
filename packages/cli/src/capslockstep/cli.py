import platform
import time

from capslockstep.key import CapsLockLinux


def main():
    match platform.system():
        case "Linux":
            caps_lock = CapsLockLinux()
        case _:
            raise NotImplementedError(f"Unsupported system: {platform.system()}")

    time.sleep(1)
    caps_lock.toggle()
    print("STATE:", caps_lock.state)

    time.sleep(1)
    caps_lock.toggle()
    print("STATE:", caps_lock.state)


if __name__ == "__main__":
    main()
