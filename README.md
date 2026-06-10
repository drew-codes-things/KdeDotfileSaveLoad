<div align="center">

# KDE Dotfiles

**A pair of Python scripts to back up and restore your KDE Plasma dotfiles - auto-detects distro, Plasma version, and session type.**

[![Python](https://img.shields.io/badge/python-3.8+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![KDE](https://img.shields.io/badge/KDE-Plasma-1d99f3?style=flat-square&logo=kde&logoColor=white)](https://kde.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

</div>

---

Two scripts - one saves, one restores. Run the save script on your current machine and it zips everything up. Run the load script on any KDE machine and pick exactly what you want back, category by category.

---

## Requirements

- Python 3.8+
- `tqdm` (`pip install tqdm`)
- KDE Plasma 5 or 6 with `plasmashell` on PATH

---

## Scripts

### KDEdotfilesSAVE/save_dotfiles.py

Detects your distro, Plasma version, and session type, then backs up all KDE config and assets into a timestamped `.zip` next to the script.

**Auto-detects:**

| Thing | How |
|---|---|
| Distro | `/etc/os-release` |
| Plasma version | `plasmashell --version` |
| Session type | `$XDG_SESSION_TYPE` / `$WAYLAND_DISPLAY` / `$DISPLAY` |

Plasma version determines whether `kservices5` or `kservices6` is included. Session type determines whether X11 files (`.Xresources`, `.xprofile`, `.xinitrc`) are included.

**Usage:**

```bash
python3 save_dotfiles.py
```

Output: `kde-dotfiles-YYYY-MM-DD_HH-MM-SS.zip` in the same folder as the script.

---

### KDEdotfilesLOAD/load_dotfiles.py

Finds all backups in `KDEdotfilesSAVE/` and lets you choose which categories to restore. Each prompt is a single keypress - no Enter needed.

**Usage:**

```bash
python3 load_dotfiles.py
```

If more than one backup exists, you pick which one first. Then for each category:

```
What would you like to restore?

  KDE core settings? [y/n]
  Desktop layout? [y/n]
  Keyboard shortcuts? [y/n]
  ...
```

---

## What Gets Saved

| Category | Paths |
|---|---|
| KDE core settings | `.config/kdeglobals`, `kwinrc`, `kwinrulesrc`, `plasmashellrc`, `ksmserverrc`, `kcminputrc`, `kscreenlockerrc` |
| Desktop layout | `.config/plasma-org.kde.plasma.desktop-appletsrc` |
| Keyboard shortcuts | `.config/kglobalshortcutsrc` |
| App configs | `.config/dolphinrc`, `konsolerc`, `katerc`, `spectaclerc`, `.local/share/konsole/` |
| Autostart | `.config/autostart/` |
| GTK settings | `.config/gtk-3.0/`, `.config/gtk-4.0/` |
| Icon & cursor themes | `.local/share/icons/`, `.icons/` |
| Fonts | `.local/share/fonts/` |
| Wallpapers | `.local/share/wallpapers/` |
| Color schemes | `.local/share/color-schemes/` |
| Window decorations | `.local/share/aurorae/` |
| Plasma themes | `.local/share/plasma/` |
| KWin scripts | `.local/share/kwin/` |
| KDE Connect | `.config/kdeconnect/` |
| Shell dotfiles | `.bashrc`, `.bash_profile`, `.zshrc`, `.profile` (+ X11 files if applicable) |

---

## Notes

- Skipped files (permission errors) are printed without stopping the run
- After restoring, log out and back in for all changes to take effect
- The load script caps backup selection at 9 entries (single keypress selection)

---

## License

MIT - made by [Drew](https://github.com/drew-codes-things)
