import pytest

from utilities.functions import find_same_objects


@pytest.mark.parametrize(
    "kwargs, strict, count, expected",
    [
        ({"a": 1, "b": 2, "c": 3}, False, 3, []),  # No duplicates
        (
            {"a": [1, 2], "b": [1, 2], "c": [1, 2], "d": [1, 2, 3]},
            False,
            2,
            [(tuple([1, 2]), ["a", "b", "c"])],
        ),
        # Non-strict equality
        (
            {"a": [1, 2], "b": [1, 2], "c": [1, 2], "d": [1, 2]},
            True,
            2,
            [],
        ),  # Strict mode (identity)
        (
            {"a": "apple", "b": "apple", "c": "banana", "d": "apple"},
            False,
            2,
            [("apple", ["a", "b", "d"])],
        ),
        # Non-strict with strings
        (
            {"a": 1, "b": 1, "c": 2},
            False,
            2,
            [(1, ["a", "b"])],
        ),  # Count with threshold met
        ({"a": 1, "b": 1, "c": 2}, False, 3, []),  # Count with threshold not met
        (
            {"a": [1, 2], "b": [1, 2], "c": [1, 2]},
            True,
            2,
            [],
        ),  # Strict mode with equal but distinct objects
    ],
)
def test_find_same_objects(kwargs, strict, count, expected):
    """Verifies the behavior of find_same_objects using parameterization."""
    result = find_same_objects(strict=strict, count=count, **kwargs)
    assert result == expected


@pytest.mark.parametrize(
    "kwargs, strict, count, expected",
    [
        ({"a": 1, "b": 2, "c": 3}, False, 3, []),  # No duplicates
        (
            {"a": [1, 2], "b": [1, 2], "c": [1, 2], "d": [1, 2, 3]},
            False,
            2,
            [(tuple([1, 2]), ["a", "b", "c"])],
        ),
        # Non-strict equality
        (
            {"a": [1, 2], "b": [1, 2], "c": [1, 2], "d": [1, 2]},
            True,
            2,
            [],
        ),  # Strict mode (identity)
        (
            {"a": "apple", "b": "apple", "c": "banana", "d": "apple"},
            False,
            2,
            [("apple", ["a", "b", "d"])],
        ),
        # Non-strict with strings
        (
            {"a": 1, "b": 1, "c": 2},
            False,
            2,
            [(1, ["a", "b"])],
        ),  # Count with threshold met
        ({"a": 1, "b": 1, "c": 2}, False, 3, []),  # Count with threshold not met
        (
            {"a": [1, 2], "b": [1, 2], "c": [1, 2]},
            True,
            2,
            [],
        ),  # Strict mode with equal but distinct objects
    ],
)
def test_find_same_objects(kwargs, strict, count, expected):
    """Verifies the behavior of find_same_objects using parameterization."""
    result = find_same_objects(strict=strict, count=count, **kwargs)
    assert result == expected


@pytest.mark.parametrize(
    "kwargs, strict, expected_obj, expected_keys",
    [
        # Strict identity check: Lists should not be grouped in strict mode.
        (
            {"a": [1, 2], "b": [1, 2], "c": [1, 2]},
            True,
            None,
            [],
        ),  # Strict mode (lists distinct by reference)
        # Tuples are immutable, so they should be grouped in strict mode even if distinct objects.
        ({"a": (1, 2), "b": (1, 2), "c": (1, 2)}, True, (1, 2), ["a", "b", "c"]),
        # Strict mode with tuples (equal by content)
        # Explicitly create lists that point to the same object
        (
            {"a": object, "b": object, "c": object},
            True,
            object,
            ["a", "b", "c"],
        ),  # Same object (same reference)
    ],
)
def test_strict_with_diff_objects(kwargs, strict, expected_obj, expected_keys):
    """Verifies the strict and non-strict behavior with different objects (including tuples)."""
    result = find_same_objects(strict=strict, count=2, **kwargs)
    if expected_obj is None:  # Ensure we handle empty results
        assert result == []
    else:
        assert len(result) == 1
        obj, keys = result[0]
        assert obj == expected_obj
        assert sorted(keys) == sorted(expected_keys)


@pytest.mark.parametrize(
    "kwargs, strict, expected",
    [
        (
            {"a": "apple", "b": "apple", "c": "banana", "d": "apple"},
            False,
            [("apple", ["a", "b", "d"])],
        ),
        # Non-strict with mixed types
        (
            {"a": [1, 2], "b": [1, 2], "c": [1, 2]},
            False,
            [(tuple([1, 2]), ["a", "b", "c"])],
        ),
        # Lists equal after conversion
    ],
)
def test_find_same_objects_non_strict(kwargs, strict, expected):
    """Verifies find_same_objects in non-strict mode with different types of values."""
    result = find_same_objects(strict=strict, count=2, **kwargs)
    assert result == expected


@pytest.mark.parametrize(
    "kwargs, strict, expected",
    [
        (
            {"a": "apple", "b": "apple", "c": "banana", "d": "apple"},
            False,
            [("apple", ["a", "b", "d"])],
        ),
        # Non-strict with mixed types
        (
            {"a": [1, 2], "b": [1, 2], "c": [1, 2]},
            False,
            [(tuple([1, 2]), ["a", "b", "c"])],
        ),
        # Lists equal after conversion
    ],
)
def test_find_same_objects_non_strict(kwargs, strict, expected):
    """Verifies find_same_objects in non-strict mode with different types of values."""
    result = find_same_objects(strict=strict, count=2, **kwargs)
    assert result == expected
