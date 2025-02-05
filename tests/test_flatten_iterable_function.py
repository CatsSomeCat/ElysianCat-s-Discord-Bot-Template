import pytest

from utilities.functions import flatten_iterable


@pytest.mark.parametrize(
    "nested_sequence, expected",
    [
        ([1, 2, [3, 4]], [1, 2, 3, 4]),  # Simple nested list
        ([1, [2, [3, 4]], 5], [1, 2, 3, 4, 5]),  # Deeply nested list
        ((1, (2, (3, 4)), 5), [1, 2, 3, 4, 5]),  # Nested tuples
        ([{1, 2}, {3, 4}], [1, 2, 3, 4]),  # Sets as elements
        (
            [1, (2, [3, {4, 5}]), 6],
            [1, 2, 3, 4, 5, 6],
        ),  # Mixed nesting (list, tuple, set)
        ([], []),  # Empty list
        ((), []),  # Empty tuple
        ([[], [[]]], []),  # Deeply nested empty lists
    ],
)
def test_flatten_iterable_basic(nested_sequence, expected):
    """Test flattening of various nested sequences."""
    assert flatten_iterable(nested_sequence) == expected


@pytest.mark.parametrize(
    "nested_sequence, disallowed_types",
    [
        ("string", (str,)),  # String should be rejected as a top-level container
        (b"bytes", (bytes,)),  # Bytes should be rejected as a top-level container
    ],
)
def test_flatten_iterable_disallowed_types(nested_sequence, disallowed_types):
    """Test that disallowed types raise a TypeError when used as a top-level container."""
    with pytest.raises(TypeError):
        flatten_iterable(nested_sequence, disallowed_types=disallowed_types)


@pytest.mark.parametrize(
    "nested_sequence, allowed_recursion, expected",
    [
        (
            [1, [2, (3, {4, 5})], 6],
            (list, tuple),
            [1, 2, 3, {4, 5}, 6],
        ),  # Stops at sets
        (
            [1, [2, (3, {4, 5})], 6],
            (list, tuple, set),
            [1, 2, 3, 4, 5, 6],
        ),  # Processes sets
    ],
)
def test_flatten_iterable_recursion_control(
    nested_sequence, allowed_recursion, expected
):
    """Test that recursion is controlled based on allowed_recursion types."""
    assert (
        flatten_iterable(nested_sequence, allowed_recursion=allowed_recursion)
        == expected
    )


def test_flatten_iterable_circular_reference():
    """Test handling of circular references (should not enter infinite loops)."""
    a = [1, 2]
    a.append(a)  # Circular reference
    result = flatten_iterable(a)
    assert result[:2] == [1, 2]  # The first elements should be preserved
    assert (
        result.count(1) == 1 and result.count(2) == 1
    )  # Circular ref shouldn't duplicate items


def test_flatten_iterable_large_input():
    """Test with large nested structures for performance and correctness."""
    large_input = [[i, [i + 1]] for i in range(1000)]
    expected_output = [i for pair in large_input for i in pair]
    assert flatten_iterable(large_input, max_depth=1) == expected_output


@pytest.mark.parametrize(
    "nested_sequence, expected",
    [
        ([1, 2, {"a": 3, "b": 4}], [1, 2, "a", "b"]),  # Dict keys should be extracted
        ({"x": [1, 2], "y": (3, 4)}, ["x", "y"]),  # Only dict keys should be flattened
    ],
)
def test_flatten_iterable_dict_handling(nested_sequence, expected):
    """Test that dictionaries are processed as sequences of keys."""
    assert flatten_iterable(nested_sequence) == expected
