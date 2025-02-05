import pytest

from exceptions import EmptyListError
from utilities.functions import format_iterable_into_human_readable_string


def test_single_item():
    """Verifies that a single item in the iterable returns that item as a string."""
    result = format_iterable_into_human_readable_string([1])
    assert result == "1"


def test_two_items_default_final():
    """Verifies the behavior for exactly two items using the default separator (', ') and the default final word ('and')."""
    result = format_iterable_into_human_readable_string([1, 2])
    assert result == "1 and 2"


def test_multiple_items_default_final():
    """Verifies the behavior for more than two items with the default separator and the default final word ('and')."""
    result = format_iterable_into_human_readable_string([1, 2, 3])
    assert result == "1, 2 and 3"


def test_multiple_items_custom_final_and_separator():
    """Verifies that a custom separator and a custom final word can be correctly used."""
    result = format_iterable_into_human_readable_string(
        [1, 2, 3], separator="; ", final="or"
    )
    assert result == "1; 2 or 3"


def test_empty_iterable():
    """Ensures that the function raises an EmptyListError if the iterable is empty."""
    with pytest.raises(
        EmptyListError, match="The 'items' iterable must contain at least one element"
    ):
        format_iterable_into_human_readable_string([], separator=", ")


def test_string_as_input():
    """Ensures that a string passed as the 'items' argument raises a TypeError."""
    with pytest.raises(
        TypeError,
        match="The 'items' parameter must not be a string. Use a list or other iterable instead",
    ):
        format_iterable_into_human_readable_string("not an iterable", separator=", ")


def test_iterable_of_strings():
    """Tests with an iterable of strings to confirm the function handles string items properly."""
    result = format_iterable_into_human_readable_string(["apple", "banana", "cherry"])
    assert result == "apple, banana and cherry"


def test_iterable_of_non_strings():
    """Tests with a list of non-string items (e.g., integers) to ensure proper conversion to string and formatting."""
    result = format_iterable_into_human_readable_string([1, 2, 3])
    assert result == "1, 2 and 3"
