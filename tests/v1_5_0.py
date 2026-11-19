"""What version 1.5.0 (aios-harness#266) moves, for the older versions' "nothing else moves" tests: National Grid's
record for wind constraint payments 2010-2015 re-splits the three balancing lines in those years, and the check
against a third party's published total is gone. The moves themselves are tested in
tests/test_national_grid_constraints.py."""
import re

MOVED = re.compile(
    r"(constraints|constraint_turnup|bsuos|direct|indirect)\.(201[0-5]|headline)\.(cash|real)"
    r"|all\.headline\.(measured|modelled|estimated)\.(cash|real)"
    r"|constraint_turnup\.range\.(low|high)\.(2015|headline)\.(cash|real)"
    r"|constraint_turnup\.cross_check\.estimate\.cash"
    r"|bsuos\.turnup_range\.(low|high)\.(2015|headline)\.(cash|real)"
    r"|option\.no_grid_balancing\.(headline|less_than_headline)\.(cash|real)")


def gone(key: str) -> bool:
    return key == "constraints.ref_years" or key.startswith("check.ref.")


def moved(key: str) -> bool:
    return bool(MOVED.fullmatch(key))


def kept(old: dict) -> dict:
    """An older version's figures less the keys 1.5.0 drops or moves."""
    return {k: v for k, v in old.items() if not gone(k) and not moved(k)}
