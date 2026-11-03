import zipfile

import pytest

import load_dotfiles
import save_dotfiles


@pytest.fixture
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(load_dotfiles, "HOME", home)
    monkeypatch.setattr(save_dotfiles, "HOME", home)
    return home


@pytest.fixture
def backup(tmp_path):
    path = tmp_path / "kde-dotfiles-2026-01-01_00-00-00.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(".config/kwinrc", "new kwin")
        zf.writestr(".config/kdeglobals", "same")
        zf.writestr(".config/autostart/app.desktop", "autostart")
        zf.writestr(".bashrc", "bash")
        zf.writestr("../escape.txt", "nope")
    return path


def snapshot(folder):
    return {str(path.relative_to(folder)): path.read_bytes() for path in folder.rglob("*") if path.is_file()}


def test_preview_reports_each_file_without_changing_anything(home, backup, capsys):
    (home / ".config").mkdir()
    (home / ".config" / "kwinrc").write_text("old kwin")
    (home / ".config" / "kdeglobals").write_text("same")
    before = snapshot(home)

    counts = load_dotfiles.preview(backup, [".config/kwinrc", ".config/kdeglobals", ".config/autostart/"])

    assert snapshot(home) == before
    assert counts == {"overwrite": 1, "unchanged": 1, "new": 1}
    out = capsys.readouterr().out
    assert "overwrite    ~/.config/kwinrc" in out
    assert "new          ~/.config/autostart/app.desktop" in out
    assert "kdeglobals" not in out


def test_preview_flags_entries_outside_home(home, backup):
    with zipfile.ZipFile(backup) as zf:
        assert load_dotfiles.restore_status(zf, "../escape.txt")[1] == "outside home"


def test_preview_with_nothing_selected(home, backup, capsys):
    assert load_dotfiles.preview(backup, [".zshrc"]) == {}
    assert "Nothing to restore." in capsys.readouterr().out


def test_restore_writes_what_preview_promised(home, backup):
    load_dotfiles.restore(backup, [".config/kwinrc", ".bashrc"])
    assert (home / ".config" / "kwinrc").read_text() == "new kwin"
    assert (home / ".bashrc").read_text() == "bash"
    assert not (home / ".config" / "kdeglobals").exists()


def test_save_preview_lists_files_and_writes_no_zip(home, tmp_path, capsys):
    (home / ".bashrc").write_text("x" * 2048)
    (home / ".config" / "kwinrc").parent.mkdir(parents=True)
    (home / ".config" / "kwinrc").write_text("abc")
    files = save_dotfiles.collect_files(6, "wayland")
    total = save_dotfiles.preview(files)
    assert total == 2051
    out = capsys.readouterr().out
    assert "~/.bashrc" in out and "2 files, 2.0 KB" in out
    assert not list(tmp_path.rglob("*.zip"))
