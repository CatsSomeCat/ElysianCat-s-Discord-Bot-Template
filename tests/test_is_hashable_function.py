import pytest

from utilities.functions import is_hashable


@pytest.mark.parametrize(
    "input_value, expected_result",
    [
        (42, True),  # Integers are hashable
        (3.14, True),  # Floats are hashable
        ("hello", True),  # Strings are hashable
        (b"bytes", True),  # Bytes are hashable
        (None, True),  # None is hashable
        (True, True),  # Booleans are hashable
        ((1, 2, 3), True),  # Tuples with hashable elements are hashable
        (frozenset({1, 2, 3}), True),  # Frozensets are hashable
        ([1, 2, 3], False),  # Lists are not hashable
        ({1, 2, 3}, False),  # Sets are not hashable
        ({"a": 1, "b": 2}, False),  # Dicts are not hashable
        (([1, 2],), False),  # Tuples containing lists are not hashable
        (({1, 2},), False),  # Tuples containing sets are not hashable
    ],
)
def test_is_hashable(input_value, expected_result):
    """Tests the is_hashable function with various inputs."""
    assert is_hashable(input_value) == expected_result
