"""Tests for Maybe helper functions."""

from __future__ import annotations

from results.core.maybe_base import Maybe
from results.maybe import flatten, get_or_insert, map_or, transpose
from results.maybe.sync import Nothing, Some


def test_flatten_some_some() -> None:
    result = flatten(Some(Some(42)))
    assert result.unwrap() == 42


def test_flatten_some_nothing() -> None:
    result: Maybe[Nothing[None]] = flatten(Some(Nothing()))
    assert result.is_nothing()


def test_flatten_nothing() -> None:
    result: Maybe[Nothing[None]] = flatten(Nothing())
    assert result.is_nothing()


def test_transpose_some() -> None:
    result = transpose(Some([1, 2, 3]))
    assert len(result) == 3
    assert result[0].unwrap() == 1
    assert result[1].unwrap() == 2
    assert result[2].unwrap() == 3


def test_transpose_nothing() -> None:
    result: list[Maybe[None]] = transpose(Nothing())
    assert result == []


def test_map_or_some() -> None:
    result = map_or(Some(5), 0, lambda x: x * 2)
    assert result == 10


def test_map_or_nothing() -> None:
    result = map_or(Nothing[None](), 99, lambda x: x * 2)
    assert result == 99


def test_get_or_insert_some() -> None:
    result = get_or_insert(Some(42), 0)
    assert result.unwrap() == 42


def test_get_or_insert_nothing() -> None:
    result = get_or_insert(Nothing(), 99)
    assert result.unwrap() == 99
