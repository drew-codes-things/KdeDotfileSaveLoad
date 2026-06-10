#!/usr/bin/env python3
import os
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

HOME = Path.home()
SCRIPT_DIR = Path(__file__).parent.resolve()


def detect_distro():
    try:
        with open("/etc/os-release") as f:
            data = {}
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    data[k] = v.strip('"')
        return data.get("PRETTY_NAME", "Unknown")
    except FileNotFoundError:
        return "Unknown"


def detect_plasma_version():
    try:
        out = subprocess.check_output(["plasmashell", "--version"], text=True, stderr=subprocess.DEVNULL)
        return int(out.split()[-1].split(".")[0])
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return None


def detect_session():
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session in ("wayland", "x11"):
        return session
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def collect_files(plasma_version, session):
    config = HOME / ".config"
    share = HOME / ".local" / "share"

    config_entries = [
        "kdeglobals", "kwinrc", "kwinrulesrc",
        "plasma-org.kde.plasma.desktop-appletsrc", "plasmashellrc",
        "kglobalshortcutsrc", "kcminputrc", "kscreenlockerrc", "ksmserverrc",
        "dolphinrc", "konsolerc", "katerc", "spectaclerc",
        "autostart", "gtk-3.0", "gtk-4.0", "kdeconnect", "menus",
    ]

    share_entries = [
        "plasma", "konsole", "color-schemes", "aurorae",
        "icons", "fonts", "kwin", "wallpapers",
        "kservices6" if (plasma_version and plasma_version >= 6) else "kservices5",
    ]

    dotfiles = [HOME / ".bashrc", HOME / ".bash_profile", HOME / ".zshrc", HOME / ".profile"]
    if session == "x11":
        dotfiles += [HOME / ".Xresources", HOME / ".xprofile", HOME / ".xinitrc"]

    roots = (
        [config / e for e in config_entries]
        + [share / e for e in share_entries]
        + [HOME / ".icons"]
        + dotfiles
    )

    files = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_dir():
            files.extend(f for f in root.rglob("*") if f.is_file())
        else:
            files.append(root)
    return files


def create_zip(files, output_path):
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in tqdm(files, unit="file", desc="Backing up", dynamic_ncols=True):
            try:
                zf.write(file, file.relative_to(HOME))
            except (PermissionError, OSError) as e:
                tqdm.write(f"  skipped: {file} ({e})")


def main():
    distro = detect_distro()
    plasma_version = detect_plasma_version()
    session = detect_session()

    print(f"Distro:   {distro}")
    print(f"Plasma:   {plasma_version or 'not detected'}")
    print(f"Session:  {session}")

    if not plasma_version:
        print("Warning: plasmashell not found — is KDE installed?")
        return

    print("Scanning files...")
    files = collect_files(plasma_version, session)
    print(f"Found:    {len(files):,} files\n")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = SCRIPT_DIR / f"kde-dotfiles-{timestamp}.zip"

    create_zip(files, output_path)
    print(f"\nSaved:    {output_path}")


if __name__ == "__main__":
    main()
