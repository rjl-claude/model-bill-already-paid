import subprocess
import sys


def test_cli_help():
    out = subprocess.run(
        [sys.executable, "-m", "billpaid", "--help"],
        capture_output=True, text=True,
    )
    assert out.returncode == 0
    for cmd in ("update", "backfill-constraints", "backfill-turnup", "results"):
        assert cmd in out.stdout

    update_help = subprocess.run(
        [sys.executable, "-m", "billpaid", "update", "--help"],
        capture_output=True, text=True)
    assert update_help.returncode == 0
    assert "bsuos" in update_help.stdout
