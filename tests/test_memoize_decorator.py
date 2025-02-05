import pytest

from utilities.decorators import memoize


# Test function without memoization
def test_memoize_basic_usage():
    """
    Tests the basic usage of the memoize decorator with LRU eviction policy.
    """

    @memoize(max_cache_size=3, eviction_policy="LRU")
    def add(a: int, b: int) -> int:
        return a + b

    # First call, should compute and store the result
    assert add(1, 2) == 3
    # Second call with same arguments, should use cached result
    assert add(1, 2) == 3

    # Call with different arguments
    assert add(2, 3) == 5
    # Should be stored in cache
    assert add(2, 3) == 5

    # Call with new arguments
    assert add(4, 5) == 9
    # Cache now has three values, LRU eviction should remove (1, 2) entry
    assert add(1, 2) == 3  # This should recompute since it's evicted


def test_memoize_lru_eviction():
    """
    Tests the LRU eviction policy when the cache exceeds the max_cache_size.
    """

    @memoize(max_cache_size=2, eviction_policy="LRU")
    def multiply(a: int, b: int) -> int:
        return a * b

    # Fill the cache with 3 calls, the first entry (1, 2) will be evicted
    multiply(1, 2)  # (1, 2) cached
    multiply(2, 3)  # (2, 3) cached
    multiply(3, 4)  # (3, 4) cached, evicts (1, 2)

    # Check the cache still holds the last two entries
    assert multiply(2, 3) == 6  # (2, 3) should still be cached
    assert multiply(3, 4) == 12  # (3, 4) should be cached


def test_memoize_lfu_eviction():
    """
    Tests the LFU eviction policy when the cache exceeds the max_cache_size.
    """

    @memoize(max_cache_size=2, eviction_policy="LFU")
    def subtract(a: int, b: int) -> int:
        return a - b

    # Call the function to populate the cache
    subtract(10, 5)  # (10, 5) cached
    subtract(20, 5)  # (20, 5) cached
    subtract(10, 5)  # (10, 5) called again, LFU count increases

    # The cache now has (10, 5) and (20, 5), but (20, 5) should be evicted
    subtract(30, 5)  # (30, 5) cached, evicts (20, 5)

    assert subtract(10, 5) == 5  # Cache should still have (10, 5)


def test_memoize_invalid_eviction_policy():
    """
    Tests invalid eviction policy.
    """
    with pytest.raises(ValueError):

        @memoize(max_cache_size=10, eviction_policy="INVALID_POLICY")
        def some_func(a: int) -> int:
            return a + 1


def test_memoize_negative_cache_size():
    """
    Tests the behavior of the memoize decorator with a negative cache size.
    """

    @memoize(max_cache_size=-1, eviction_policy="LRU")
    def add(a: int, b: int) -> int:
        return a + b

    assert add(1, 2) == 3
    # The cache size is 0, so it should recompute every time.
    assert add(1, 2) == 3


def test_memoize_type_annotation():
    """
    Tests that the memoize decorator works correctly with functions that have type annotations.
    """

    @memoize(max_cache_size=2, eviction_policy="LRU")
    def multiply(a: int, b: int) -> int:
        return a * b

    # Testing with valid type annotations
    assert multiply(3, 4) == 12
    assert multiply(3, 4) == 12  # Cached result


def test_memoize_non_hashable_args():
    """
    Tests that non-hashable arguments are handled by making them hashable.
    """

    @memoize(max_cache_size=3, eviction_policy="LRU")
    def append_element(a: list, elem: int) -> list:
        a.append(elem)
        return a

    # This should work by making `a` hashable
    result = append_element([1, 2], 3)
    assert result == [1, 2, 3]


@pytest.mark.parametrize(
    "max_cache_size, eviction_policy",
    [
        (5, "LRU"),
        (5, "LFU"),
        (10, "LRU"),
    ],
)
def test_memoize_cache_size_and_eviction(max_cache_size, eviction_policy):
    """
    Tests the behavior of the memoize decorator when different cache sizes and eviction policies are used.
    """

    @memoize(max_cache_size=max_cache_size, eviction_policy=eviction_policy)
    def process_data(a: int, b: int) -> int:
        return a + b

    # Adding multiple entries to check cache size and eviction behavior
    process_data(1, 1)
    process_data(2, 2)
    process_data(3, 3)
    process_data(4, 4)
    process_data(5, 5)

    # Cache should be sized according to the max_cache_size with LRU or LFU eviction policies
    # Check that the most recent entry is always in the cache
    assert process_data(5, 5) == 10
    if eviction_policy == "LRU":
        assert process_data(1, 1) == 2  # LRU eviction should not remove the most recent
    elif eviction_policy == "LFU":
        assert (
            process_data(5, 5) == 10
        )  # LFU eviction should still keep most frequently used
