"""WHATIF lane entry point. Set IMPLEMENTED = True once tests pass."""

from __future__ import annotations

from backend.app.contracts import Node, Session, WhatIfResult

IMPLEMENTED = False


class WhatIf:
    def simulate(self, session: Session, path: list[Node], node_id: str) -> WhatIfResult:
        raise NotImplementedError


def get_service() -> WhatIf:
    return WhatIf()
