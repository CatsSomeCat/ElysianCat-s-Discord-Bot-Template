import pytest

from utilities.functions import flatten_dict_no_hierarchy_iterative


@pytest.fixture
def sample_nested_dict():
    """Returns a sample nested dictionary for testing."""
    return {"a": 1, "b": {"c": 2, "d": 3}, "e": {"f": {"g": 4}, "h": 5}}


@pytest.fixture
def sample_flat_dict():
    """Returns a sample flat dictionary for testing."""
    return {"x": 10, "y": 20}


@pytest.mark.parametrize(
    "nested_dict, expected_dict",
    [
        (
            {"a": 1, "b": {"c": 2, "d": 3}, "e": {"f": {"g": 4}, "h": 5}},
            {"a": 1, "c": 2, "d": 3, "g": 4, "h": 5},
        ),
        ({}, {}),
        ({"a": {}, "b": {"c": {}}}, {}),
    ],
)
def test_flatten_dict_dict(nested_dict, expected_dict):
    """Tests the function for flattening into a dictionary."""
    assert (
        flatten_dict_no_hierarchy_iterative(nested_dict, return_type="dict")
        == expected_dict
    )


@pytest.mark.parametrize(
    "nested_dict, expected_list",
    [
        (
            {"a": 1, "b": {"c": 2, "d": 3}, "e": {"f": {"g": 4}, "h": 5}},
            list({"a": 1, "c": 2, "d": 3, "g": 4, "h": 5}.items()),
        ),
        ({}, []),
        ({"a": {}, "b": {"c": {}}}, []),
    ],
)
def test_flatten_dict_list_of_tuples(nested_dict, expected_list):
    """Tests the function for flattening into a list of tuples."""
    assert (
        flatten_dict_no_hierarchy_iterative(nested_dict, return_type="list_of_tuples")
        == expected_list
    )


@pytest.mark.parametrize(
    "nested_dict, expected_tuple",
    [
        (
            {"a": 1, "b": {"c": 2, "d": 3}, "e": {"f": {"g": 4}, "h": 5}},
            (
                list({"a": 1, "c": 2, "d": 3, "g": 4, "h": 5}.keys()),
                list({"a": 1, "c": 2, "d": 3, "g": 4, "h": 5}.values()),
            ),
        ),
        ({}, ([], [])),
        ({"a": {}, "b": {"c": {}}}, ([], [])),
    ],
)
def test_flatten_dict_tuple_of_lists(nested_dict, expected_tuple):
    """Tests the function for flattening into a tuple of lists."""
    assert (
        flatten_dict_no_hierarchy_iterative(nested_dict, return_type="tuple_of_lists")
        == expected_tuple
    )


def test_flatten_dict_flat(sample_flat_dict):
    """Tests a flat dictionary which should remain unchanged."""
    assert (
        flatten_dict_no_hierarchy_iterative(sample_flat_dict, return_type="dict")
        == sample_flat_dict
    )


def test_flatten_dict_invalid_type(sample_nested_dict):
    """Tests the function with an invalid return type, expecting a ValueError."""
    with pytest.raises(ValueError, match="Unsupported return_type: invalid_type."):
        flatten_dict_no_hierarchy_iterative(
            sample_nested_dict, return_type="invalid_type"
        )
