#!/usr/bin/env python3
import argparse
import sys
from collections import Counter
import tty
import termios
import zipfile
from pathlib import Path

from tqdm import tqdm

HOME = Path.home()
SCRIPT_DIR = Path(__file__).parent.resolve()
SAVE_DIRS = [SCRIPT_DIR, SCRIPT_DIR.parent / "KDEdotfilesSAVE"]
MAX_LISTED_BACKUPS = 9

CATEGORIES = [
    ("KDE core settings",    [".config/kdeglobals", ".config/kwinrc", ".config/kwinrulesrc",
                               ".config/plasmashellrc", ".config/ksmserverrc",
                               ".config/kcminputrc", ".config/kscreenlockerrc"]),
    ("Desktop layout",       [".config/plasma-org.kde.plasma.desktop-appletsrc"]),
    ("Keyboard shortcuts",   [".config/kglobalshortcutsrc"]),
    ("App configs",          [".config/dolphinrc", ".config/konsolerc", ".config/katerc",
                               ".config/spectaclerc", ".local/share/konsole/"]),
    ("Autostart",            [".config/autostart/"]),
    ("GTK settings",         [".config/gtk-3.0/", ".config/gtk-4.0/"]),
    ("Icon & cursor themes", [".local/share/icons/", ".icons/"]),
    ("Fonts",                [".local/share/fonts/"]),
    ("Wallpapers",           [".local/share/wallpapers/"]),
    ("Color schemes",        [".local/share/color-schemes/"]),
    ("Window decorations",   [".local/share/aurorae/"]),
    ("Plasma themes",        [".local/share/plasma/"]),
    ("KWin scripts",         [".local/share/kwin/"]),
    ("KDE Connect",          [".config/kdeconnect/"]),
    ("Shell dotfiles",       [".bashrc", ".bash_profile", ".zshrc", ".profile",
                               ".Xresources", ".xprofile", ".xinitrc"]),
]


def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def ask_yn(prompt):
    print(prompt + " [y/n] ", end="", flush=True)
    while True:
        key = getch()
        if key in ("y", "n"):
            print(key)
            return key == "y"


def select_backup(backups):
    if len(backups) == 1:
        print(f"Using: {backups[0].name}\n")
        return backups[0]

    cap = min(len(backups), MAX_LISTED_BACKUPS)

    print("Available backups (newest first):")
    for i, backup in enumerate(backups[:cap], 1):
        print(f"  {i}. {backup.name}")
    print(f"\nSelect [1-{cap}]: ", end="", flush=True)

    valid = [str(i) for i in range(1, cap + 1)]
    while True:
        key = getch()
        if key in valid:
            print(key)
            return backups[int(key) - 1]


def entry_matches(entry, prefixes):
    for prefix in prefixes:
        if prefix.endswith("/"):
            if entry.startswith(prefix):
                return True
        elif entry == prefix:
            return True
    return False


def restore_status(zf, entry):
    dest = (HOME / entry).resolve()
    if not dest.is_relative_to(HOME.resolve()):
        return dest, "outside home"
    if not dest.exists():
        return dest, "new"
    try:
        if dest.is_file() and dest.read_bytes() == zf.read(entry):
            return dest, "unchanged"
    except OSError:
        return dest, "unreadable"
    return dest, "overwrite"


def preview(zip_path, selected_prefixes):
    with zipfile.ZipFile(zip_path) as zf:
        entries = [e for e in zf.namelist() if entry_matches(e, selected_prefixes)]
        statuses = [(entry, restore_status(zf, entry)[1]) for entry in entries]
    if not statuses:
        print("Nothing to restore.")
        return Counter()
    for entry, status in statuses:
        if status != "unchanged":
            print(f"  {status:<12} ~/{entry}")
    counts = Counter(status for _, status in statuses)
    print("\n" + ", ".join(f"{count} {status}" for status, count in sorted(counts.items())))
    print("Dry run: nothing was changed.")
    return counts


def restore(zip_path, selected_prefixes):
    with zipfile.ZipFile(zip_path) as zf:
        to_restore = [e for e in zf.namelist() if entry_matches(e, selected_prefixes)]
        if not to_restore:
            print("Nothing to restore.")
            return
        for entry in tqdm(to_restore, unit="file", desc="Restoring", dynamic_ncols=True):
            dest = (HOME / entry).resolve()
            if not dest.is_relative_to(HOME.resolve()):
                tqdm.write(f"  skipped: {entry} (points outside your home folder)")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest.write_bytes(zf.read(entry))
                restore_permissions(dest, zf.getinfo(entry))
            except (PermissionError, OSError) as e:
                tqdm.write(f"  skipped: {dest} ({e})")


def restore_permissions(dest, info):
    mode = (info.external_attr >> 16) & 0o777
    if mode:
        dest.chmod(mode)


def parse_args():
    parser = argparse.ArgumentParser(description="Restore KDE settings from a kde-dotfiles backup.")
    parser.add_argument("--dry-run", action="store_true",
                        help="List which files would be created or overwritten, without changing anything")
    return parser.parse_args()


def main():
    args = parse_args()
    found = {path.resolve() for folder in SAVE_DIRS for path in folder.glob("kde-dotfiles-*.zip")}
    backups = sorted(found, key=lambda path: path.name, reverse=True)
    if not backups:
        print(f"No backups found in {' or '.join(str(folder) for folder in SAVE_DIRS)}")
        sys.exit(1)

    zip_path = select_backup(backups)

    print("What would you like to restore?\n")
    selected_prefixes = []
    for name, prefixes in CATEGORIES:
        if ask_yn(f"  {name}?"):
            selected_prefixes.extend(prefixes)

    if not selected_prefixes:
        print("\nNothing selected.")
        sys.exit(0)

    print()
    if args.dry_run:
        preview(zip_path, selected_prefixes)
        return
    restore(zip_path, selected_prefixes)
    print("\nDone. You may need to log out and back in for changes to take effect.")


if __name__ == "__main__":
    main()
