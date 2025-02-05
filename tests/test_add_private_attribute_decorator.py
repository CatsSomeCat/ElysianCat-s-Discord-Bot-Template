import pytest

from utilities.decorators import add_private_attributes


@pytest.mark.parametrize(
    "attrs, expected_attributes",
    [
        (
            {"attr1": 42, "attr2": "hello"},
            {"_attr1": 42, "_attr2": "hello"},
        ),  # Multiple attributes
        ({"value": 100}, {"_value": 100}),  # Single attribute
        ({}, {}),  # No attributes
    ],
)
def test_add_private_attributes(attrs, expected_attributes):
    """Tests that the decorator correctly adds private attributes to a function."""

    @add_private_attributes(**attrs)
    def sample_function():
        return "test"

    # Check if the attributes were added
    for attr, expected_value in expected_attributes.items():
        assert hasattr(sample_function, attr), f"Function is missing attribute: {attr}"
        assert (
            getattr(sample_function, attr) == expected_value
        ), f"Unexpected value for {attr}"


def test_add_private_attributes_with_invalid_name():
    """Tests that the decorator raises a ValueError when an attribute starts with an underscore."""
    with pytest.raises(ValueError, match="must not start with an underscore"):

        @add_private_attributes(_invalid=123)
        def sample_function():
            return "test"


def test_add_private_attributes_on_non_callable():
    """Tests that the decorator raises a TypeError when applied to a non-callable object."""
    with pytest.raises(
        TypeError, match="The decorator can only be applied to callable objects"
    ):
        add_private_attributes(attr=123)(42)  # Applying decorator to an int


def test_decorated_function_execution():
    """Tests that the decorated function executes correctly after adding attributes."""

    @add_private_attributes(custom_attr="data")
    def sample_function():
        return "executed"

    assert sample_function() == "executed", "Function did not execute properly"
