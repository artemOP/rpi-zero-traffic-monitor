from typing import Any


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, value: object) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()

__all__ = ("MISSING",)
