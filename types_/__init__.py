from __future__ import annotations

from typing import (
    Any,
    AsyncContextManager,
    AsyncIterable,
    Awaitable,
    Callable,
    ContextManager,
    Coroutine,
    Dict,
    Iterable,
    List,
    Optional,
    ParamSpec,
    Set,
    Tuple,
    TypeVar,
    Union,
)

# Define invariant type variables for generic types
T = TypeVar("T", covariant=False, contravariant=False)  # Represents a generic type
U = TypeVar(
    "U", covariant=False, contravariant=False
)  # Represents a second generic type
V = TypeVar(
    "V", covariant=False, contravariant=False
)  # Represents a third generic type

# Define a parameter specification variable for capturing function signatures
# This is useful for preserving the argument types of callables in higher-order functions
P = ParamSpec("P")

# Define a type for functions that may return either a value or an awaitable value
# This is useful for functions that can be either synchronous or asynchronous
MaybeAwaitableFunc = Callable[P, Union[T, Awaitable[T]]]

# Define a type alias for coroutines that return a value of type 'T'
# This is a shorthand for Coroutine[Any, Any, T], which is the most common coroutine type
Coro = Coroutine[Any, Any, T]

# Define a type alias for coroutine functions (async functions)
# These are functions that return a coroutine when called
CoroFunc = Callable[..., Coro[Any]]

# Define a type for values that may be either a value of type 'T' or a coroutine yielding 'T'
# This is useful for APIs that accept both synchronous and asynchronous values
MaybeCoro = Union[T, Coro[T]]

# Define a type for values that may be either a value of type 'T' or an awaitable yielding 'T'
# This is a more general version of MaybeCoro, including any awaitable (not just coroutines)
MaybeAwaitable = Union[T, Awaitable[T]]

# Define a recursive type alias for nested sequences
NestedSequence = Union[
    Any,
    List["NestedSequence"],
    Tuple["NestedSequence", ...],
    Set["NestedSequence"],
    Dict[Any, "NestedSequence"],
]

# Define a type for optional values, which can either be of type 'T' or None
# This is a common pattern for representing values that may be absent
OptionalT = Union[T, None]

# Define a type for functions that take no arguments and return a value of type 'T'
# This is useful for representing thunks or lazy evaluations
Thunk = Callable[[], T]

# Define a type for functions that take a single argument of type 'T' and return a value of type 'U'
# This is useful for representing unary transformations
UnaryFunc = Callable[[T], U]

# Define a type for functions that take two arguments of types 'T' and 'U' and return a value of type 'V'
# This is useful for representing binary operations
BinaryFunc = Callable[[T, U], V]

# Define a type for dictionaries where keys are strings and values are of type 'T'
# This is useful for representing JSON-like structures or configuration objects
StringDict = Dict[str, T]

# Define a type for sequences that can be either a list or a tuple of elements of type 'T'
# This is useful for APIs that accept both mutable and immutable sequences
SequenceT = Union[List[T], Tuple[T, ...]]

# Define a type for iterables that yield elements of type 'T'
# This is useful for representing generators or other iterable collections
IterableT = Iterable[T]

# Define a type for asynchronous iterables that yield elements of type 'T'
# This is useful for representing asynchronous generators or streams
AsyncIterableT = AsyncIterable[T]

# Define a type for context managers that yield values of type 'T'
# This is useful for representing resources that need to be managed
ContextManagerT = ContextManager[T]

# Define a type for asynchronous context managers that yield values of type 'T'
# This is useful for representing asynchronous resources
AsyncContextManagerT = AsyncContextManager[T]

# Define a type for functions that take a variable number of arguments and return a value of type 'T'
# This is useful for representing variadic functions
VariadicFunc = Callable[..., T]

# Define a type for functions that take no arguments and return a coroutine yielding a value of type 'T'
# This is useful for representing asynchronous thunks
AsyncThunk = Callable[[], Coro[T]]

# Define a type for functions that take a single argument of type 'T' and return a coroutine yielding a value of type 'U'
# This is useful for representing asynchronous unary transformations
AsyncUnaryFunc = Callable[[T], Coro[U]]

# Define a type for functions that take two arguments of types 'T' and 'U' and return a coroutine yielding a value of type 'V'
# This is useful for representing asynchronous binary operations
AsyncBinaryFunc = Callable[[T, U], Coro[V]]
