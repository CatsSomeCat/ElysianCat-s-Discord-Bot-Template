import pytest

from utilities.functions import is_palindrome


@pytest.mark.parametrize(
    "input_string, expected_result",
    [
        # Basic palindromes
        ("racecar", True),  # Simple palindrome
        ("madam", True),  # Another simple palindrome
        ("level", True),  # Palindrome with odd number of characters
        # Palindromes with non-alphanumeric characters
        (
            "A man, a plan, a canal, Panama",
            True,
        ),  # Palindrome with punctuation and spaces
        ("No 'x' in Nixon", True),  # Palindrome with spaces and quotes
        (
            "Was it a car or a cat I saw?",
            True,
        ),  # Palindrome with punctuation and spaces
        # Case-insensitive check
        ("Able was I ere I saw Elba", True),  # Case-insensitive palindrome
        # Non-palindromes
        ("hello", False),  # Not a palindrome
        ("world", False),  # Not a palindrome
        # Edge cases
        ("", True),  # Empty string is considered a palindrome
        ("a", True),  # Single character string is a palindrome
        ("ab", False),  # Two different characters
    ],
)
def test_is_palindrome(input_string, expected_result):
    """Verifies that the 'is_palindrome' function works as expected."""
    assert is_palindrome(input_string) == expected_result
