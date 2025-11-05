from __future__ import annotations

from typing import Callable, Generic, Optional, TypeVar, cast

L = TypeVar("L")  # Left type (error)
R = TypeVar("R")  # Right type (success)
T = TypeVar("T")


class Either(Generic[L, R]):
    """Represents a value that can either be a success (Right) or an error (Left)."""

    def __init__(self) -> None:
        self._left: Optional[L] = None
        self._right: Optional[R] = None
        self._is_left: bool = False

    def is_left(self) -> bool:
        return self._is_left

    def is_right(self) -> bool:
        return not self._is_left

    def get_left(self) -> L:
        if not self.is_left():
            raise ValueError(
                "Não é um Left. Verifique com 'is_left()' antes de chamar 'get_left()'."
            )
        return cast(L, self._left)

    def get_right(self) -> R:
        if not self.is_right():
            raise ValueError(
                "Não é um Right. Verifique com 'is_right()' antes de chamar 'get_right()'."
            )
        return cast(R, self._right)

    @staticmethod
    def as_left(value: L) -> "Either[L, R]":
        e: "Either[L, R]" = Either()
        e._left = value
        e._is_left = True
        return e

    @staticmethod
    def as_right(value: R) -> "Either[L, R]":
        e: "Either[L, R]" = Either()
        e._right = value
        e._is_left = False
        return e

    def map(self, func: Callable[[R], T]) -> "Either[L, T]":
        if self.is_right():
            return Either.as_right(func(self.get_right()))
        return Either.as_left(self.get_left())

    def flat_map(self, func: Callable[[R], "Either[L, T]"]) -> "Either[L, T]":
        if self.is_right():
            return func(self.get_right())
        return Either.as_left(self.get_left())


Right = Either.as_right
Left = Either.as_left
