import sys
import os
import shutil
import time
from datetime import datetime
import argparse


def vytvor_logfile_name():
    """iba vygeneruje nazev log souboru"""
    start_time_str = datetime.now().strftime("%Y%m%d_%H%M")
    return f"sync_adrs_{start_time_str}.log"


def zapis_do_logu(action, soubor, log_file, error_message=None):
    """vytvori zapis do logu a to same vypise do konzole"""
    curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if error_message:
        log_zaznam = f"[{curr_time}] -- {action} -- {soubor} ({error_message})"
    else:
        log_zaznam = f"[{curr_time}] -- {action} -- {soubor}"

    print(log_zaznam)
    with open(log_file, 'a') as log:
        log.write(log_zaznam + "\n")


def normalizuj_adresar(adresar):
    """normalizuje adresare"""
    adresar = adresar.replace("\\", os.sep).replace("/", os.sep)
    return os.path.normpath(adresar)

def addr_ok(adresar, log_file):
    """
    Kontroluje, ci adresar je adresar, ma prava na citanie a prechadzanie.
    Existenciu nekontroluje, ta sa kontroluje zvlast, lebo inak sa chova script pre zdrojovy a inak pre cielovy adrear.
    Loguje vysledky kontroly.
    """
    if not os.path.isdir(adresar):
        zapis_do_logu("ERROR", f"Adresar '{adresar}' neni adresar.", log_file)
        return False

    if not os.access(adresar, os.R_OK):
        zapis_do_logu("ERROR", f"Adresar '{adresar}' neni pristupny k cteni pro Vas.", log_file)
        return False

    if not os.access(adresar, os.X_OK):
        zapis_do_logu("ERROR", f"Adresar '{adresar}' neni pristupny k prochazeni pro Vas.", log_file)
        return False

    zapis_do_logu("OK", f"Adresar '{adresar}' je validny a pristupny.", log_file)
    return True

def synchronizuj_adresare(source_dir, target_dir, log_file):
    """
    samotna synchronizacia adresarov
    samozrejme pred tym kontrola existencie a podmienok
    spocitava aktualizovane, zmenene, zmazane a zapise v summary do logu
    """
    source_dir = normalizuj_adresar(source_dir)
    target_dir = normalizuj_adresar(target_dir)
    if not os.path.exists(source_dir):
        zapis_do_logu("ERROR", f"Zdrojový adresár '{source_dir}' neexistuje.", log_file)
        sys.exit(1)

    if not addr_ok(source_dir, log_file):
        zapis_do_logu("ERROR", f"Zdrojovy adresar '{source_dir}' nevyhovuje podminkam.", log_file)
        sys.exit(1)

    if not addr_ok(target_dir, log_file):
        zapis_do_logu("ERROR", f"Cielovy adresar '{target_dir}' nevyhovuje podminkam.", log_file)
        sys.exit(1)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir, mode=0o777)
        shutil.copystat(source_dir, target_dir)
        zapis_do_logu("CREATED DIRECTORY", target_dir, log_file)

    kopirovane = 0
    aktualizovane = 0
    zmazane = 0

    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        target_root = os.path.join(target_dir, rel_path)

        if not os.path.exists(target_root):
            os.makedirs(target_root)
            shutil.copystat(root, target_root)
            zapis_do_logu("CREATED DIRECTORY", target_root, log_file)

        for file in files:
            source_file = os.path.join(root, file)
            target_file = os.path.join(target_root, file)

            if not os.path.exists(target_file):
                try:
                    shutil.copy2(source_file, target_file)
                    kopirovane += 1
                    zapis_do_logu("COPIED", source_file, log_file)
                except Exception as e:
                    zapis_do_logu("COPY FAILED", source_file, log_file, str(e))
            else:
                if os.path.getmtime(source_file) > os.path.getmtime(target_file):
                    try:
                        shutil.copy2(source_file, target_file)
                        aktualizovane += 1
                        zapis_do_logu("UPDATED", source_file, log_file)
                    except Exception as e:
                        zapis_do_logu("UPDATE FAILED", source_file, log_file, str(e))
                elif os.path.getmtime(source_file) < os.path.getmtime(target_file):
                    zapis_do_logu("NEWER THAN SOURCE", target_file, log_file)

    for root, dirs, files in os.walk(target_dir, topdown=False):
        rel_path = os.path.relpath(root, target_dir)
        source_root = os.path.join(source_dir, rel_path)

        for file in files:
            target_file = os.path.join(root, file)
            source_file = os.path.join(source_root, file)

            if not os.path.exists(source_file):
                try:
                    os.remove(target_file)
                    zmazane += 1
                    zapis_do_logu("DELETED", target_file, log_file)
                except Exception as e:
                    zapis_do_logu("DELETE FAILED", target_file, log_file, str(e))

        for dir in dirs:
            target_subdir = os.path.join(root, dir)
            source_subdir = os.path.join(source_root, dir)

            if not os.path.exists(source_subdir):
                try:
                    shutil.rmtree(target_subdir)
                    zmazane += 1
                    zapis_do_logu("DELETED DIRECTORY", target_subdir, log_file)
                except Exception as e:
                    zapis_do_logu("DELETE DIRECTORY FAILED", target_subdir, log_file, str(e))

    return kopirovane, aktualizovane, zmazane


def is_locked(lock_file):
    return os.path.exists(lock_file)


def create_lock(lock_file):
    """
    vytvori lock soubor, ktory zabrani, aby sa spustila druha instancia scriptu
    """
    with open(lock_file, 'w') as lock:
        lock.write(f"Locked by process {os.getpid()} at {datetime.now()}")


def release_lock(lock_file):
    if os.path.exists(lock_file):
        os.remove(lock_file)


def main():
    parser = argparse.ArgumentParser(description="Synchronizácia adresárov.")
    parser.add_argument("--zdr_adr", required=True, help="Zdrojový adresár. (bez lomitka na konci)")
    parser.add_argument("--cil_adr", required=True, help="Cieľový adresár. (bez lomitka na konci)")
    parser.add_argument("--perioda", type=int, default=0, help="Perióda spúšťania (v minútach).")
    parser.add_argument("--sync_log", default=vytvor_logfile_name(), help="Názov logovacieho súboru.")

    args = parser.parse_args()

    args.zdr_adr = normalizuj_adresar(args.zdr_adr)
    args.cil_adr = normalizuj_adresar(args.cil_adr)

    source_dir = args.zdr_adr
    target_dir = args.cil_adr

    stop_lock = "stop.lock"
    lock_file = "sync.lock"

    if is_locked(lock_file):
        print("Skript už beží. Ukončujem.")
        zapis_do_logu("SKIP", "Skript už beží", args.sync_log)
        sys.exit(1)

    create_lock(lock_file)
    try:
        while True:
            zapis_do_logu("START SYNC", "", args.sync_log)
            kopirovane, aktualizovane, zmazane = synchronizuj_adresare(source_dir, target_dir, args.sync_log)
            zapis_do_logu("SUMMARY", f"Copied: {kopirovane}, Updated: {aktualizovane}, Deleted: {zmazane}",
                          args.sync_log)
            zapis_do_logu("END SYNC", "", args.sync_log)

            if os.path.exists(stop_lock):
                zapis_do_logu("STOP", "Proces bol zastavený cez stop.lock", args.sync_log)
                os.remove(stop_lock)
                zapis_do_logu("STOP", "Stop.lock bol odstraneny", args.sync_log)
                break

            if args.perioda <= 0:
                break

            time.sleep(args.perioda * 60)
    finally:
        release_lock(lock_file)
        if os.path.exists(stop_lock):
            os.remove(stop_lock)


# sys.argv = [
#     'Test_task_debug.py',
#     '--zdr_adr', 'c:\\Users\\BigBrother\\PycharmProjects\\python\\Norbert_H\\',
#     '--cil_adr', 'c:\\Users\\BigBrother\\_copy_test2\\',
#     '--perioda', '10',
#     '--sync_log', 'sync_log.txt'
# ]

if __name__ == "__main__":
    main()
