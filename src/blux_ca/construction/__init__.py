"""cA 2 construction and repair engine for BLUX (docs/CONSTRUCTION.md).

cA turns explicit instructions (a blueprint ordered by a CogA plan, structured edits, unified diffs,
configuration data, or DAT findings) into a minimal, auditable `ca.changeset`, and applies it to a
workspace transactionally, keeping rollback artifacts. cA never certifies its own work: every result
says `certified: false` and names DAT as the validator.
"""

from blux_ca.construction.api import CAPABILITIES, run
from blux_ca.construction.common import ENGINE_VERSION, CaError

__all__ = ["CAPABILITIES", "ENGINE_VERSION", "CaError", "run"]
