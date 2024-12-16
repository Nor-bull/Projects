import os
import sys
from datetime import datetime

def vytvor_stop(lock_file):
    with open(lock_file, 'w') as f:
        f.write(f"Stop requested at {datetime.now()}\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pomocný skript na zastavenie hlavného skriptu.")
    parser.add_argument("--main_script", required=True, help="Názov hlavného skriptu.")
    args = parser.parse_args()

    main_script = args.main_script
    stop_lock = "stop.lock"

    if not os.path.exists(main_script):
        print(f"Hlavný skript '{main_script}' sa nenašiel v aktuálnom adresári ({os.getcwd()}).")
        sys.exit(1)

    if not os.path.exists(stop_lock):
        vytvor_stop(stop_lock)
        print(f"Stop lock '{stop_lock}' bol úspešne vytvorený.")
    else:
        print(f"Stop lock '{stop_lock}' už existuje.")

if __name__ == "__main__":
    main()
