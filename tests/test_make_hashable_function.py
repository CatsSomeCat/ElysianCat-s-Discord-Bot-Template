from typing import Any, Hashable

import pytest

from utilities.functions import make_hashable


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        # Test case 1: Hashable primitive types
        (42, 42),  # Integer
        ("hello", "hello"),  # String
        (3.14, 3.14),  # Float
        (True, True),  # Boolean
        (None, None),  # NoneType
        (b"bytes", b"bytes"),  # Bytes
        # Test case 2: Lists and Tuples
        ([1, 2, 3], (1, 2, 3)),  # List -> Tuple
        ((4, 5, 6), (4, 5, 6)),  # Tuple remains Tuple
        ([["a", "b"], ["c", "d"]], (("a", "b"), ("c", "d"))),  # Nested lists
        # Test case 3: Dictionaries
        ({"a": 1, "b": 2}, frozenset({("a", 1), ("b", 2)})),  # Dict -> frozenset
        ({"x": {"y": 3}}, frozenset({("x", frozenset({("y", 3)}))})),  # Nested dicts
        # Test case 4: Sets and Frozensets
        ({1, 2, 3}, frozenset({1, 2, 3})),  # Set -> frozenset
        (frozenset({4, 5, 6}), frozenset({4, 5, 6})),  # Frozenset remains unchanged
        # Test case 5: Mixed structures
        (
            [{"a": [1, 2]}, {"b": {3, 4}}],
            ((frozenset({("a", (1, 2))})), (frozenset({("b", frozenset({3, 4}))}))),
        ),
        # Nested lists & dicts
    ],
)
def test_make_hashable_valid_cases(input_value: Any, expected_output: Hashable):
    """
    Tests that make_hashable correctly converts various inputs into hashable types.
    """
    assert make_hashable(input_value) == expected_output


@pytest.mark.parametrize(
    "input_value",
    [
        pytest.param(
            lambda: {1, [2, 3]}, id="set_with_unhashable_list"
        ),  # Set containing an unhashable list
        # pytest.param(lambda: {"a": [1, 2]}, id = "dict_with_unhashable_list"),  # Dict containing an unhashable list
        pytest.param(
            lambda: {frozenset(): "valid", []: "invalid"}, id="dict_with_unhashable_key"
        ),
        # Dict with unhashable key
        pytest.param(
            lambda: {{1, 2}: "invalid"}, id="dict_with_unhashable_set_key"
        ),  # Dict with set as a key
    ],
)
def test_make_hashable_raises_type_error(input_value: Any):
    """
    Tests that make_hashable raises TypeError for unhashable inputs.
    """
    with pytest.raises(TypeError):
        make_hashable(input_value())  # Call lambda to delay evaluation
