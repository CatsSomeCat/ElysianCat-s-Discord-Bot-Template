import pytest

from exceptions import ValidationSignatureError
from utilities.decorators import validate_input


# Define the validation function and the target function
def validation_func(x):
    return x > 0


def target_func(x):
    return x + 1


# Define a function with a mismatched signature
def mismatched_target_func(x, y):
    return x + y


@pytest.mark.parametrize(
    "validation_func, target_func, input_args, expected_result, raises_error",
    [
        # Test case 1: Valid input, should pass validation
        (
            validation_func,
            target_func,
            (5,),
            6,
            None,
        ),  # Test: Positive number validation
        # Test case 2: Invalid input, validation fails
        (
            validation_func,
            target_func,
            (-1,),
            None,
            ValueError,
        ),  # Test: Negative number validation failure
        # Test case 3: Signature mismatch between validation and target function
        (
            validation_func,
            mismatched_target_func,
            (5,),
            None,
            ValidationSignatureError,
        ),  # Test: Signature mismatch
    ],
)
def test_validate_input(
    validation_func, target_func, input_args, expected_result, raises_error
):
    """
    Tests the validate_input decorator to ensure the decorated function executes correctly when input is valid.
    """
    if raises_error:
        with pytest.raises(raises_error):
            # Decorate the function and call it with the provided arguments
            decorated_func = validate_input(validation_func)(target_func)
            decorated_func(*input_args)  # This should raise the expected error
    else:
        # Decorate the function and call it with the provided arguments
        decorated_func = validate_input(validation_func)(target_func)
        result = decorated_func(*input_args)
        assert result == expected_result


@pytest.mark.parametrize(
    "validation_func, target_func, input_args, expected_result, raises_error",
    [
        # Test case 1: Signature mismatch between validation and target function
        (
            validation_func,
            mismatched_target_func,
            (5,),
            None,
            ValidationSignatureError,
        ),  # Test: Signature mismatch
    ],
)
def test_validate_input_signature_mismatch(
    validation_func, target_func, input_args, expected_result, raises_error
):
    """
    Tests the validate_input decorator to ensure it raises ValidationSignatureError on signature mismatch.
    """
    # Ensure that the exception is raised as expected
    with pytest.raises(raises_error):
        # Decorate the function and call it with the provided arguments
        decorated_func = validate_input(validation_func)(target_func)
        decorated_func(*input_args)
