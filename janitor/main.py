import time

import redis

r = redis.Redis(host="redis", port=6379, db=0)


def clean_up_ticks():
    keys = r.keys("tick:*")

    # Sort the keys based on the numeric value after "tick:"
    sorted_keys = sorted(keys, key=lambda k: int(k.decode().split(":")[1]))

    # If there are more than 3 keys, delete all but the last 3
    if len(sorted_keys) > 3:
        keys_to_delete = sorted_keys[:-3]
        r.delete(*keys_to_delete)

        tick_numbers_only = [int(k.decode().split(":")[1]) for k in sorted_keys[:-3]]
        print(f"Janitor deleted ticks: {tick_numbers_only}", flush=True)


def main():
    while True:
        clean_up_ticks()
        time.sleep(30)


if __name__ == "__main__":
    main()
