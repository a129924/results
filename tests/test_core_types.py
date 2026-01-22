"""Unit tests for core type variables.

This test module validates that type variables are correctly defined
and properly configured for use in the Result framework.
"""

from results.core.types import E, F, T, U


class TestTypeVariables:
    """Tests for core type variable definitions."""

    def test_t_is_type_var(self) -> None:
        """T should be a TypeVar with no constraints."""
        # TypeVars are instances of typing.TypeVar
        assert hasattr(T, "__name__")
        assert T.__name__ == "T"
        assert T.__bound__ is None

    def test_e_is_type_var_bound_to_exception(self) -> None:
        """E should be a TypeVar bound to Exception."""
        assert hasattr(E, "__name__")
        assert E.__name__ == "E"
        assert E.__bound__ is Exception

    def test_u_is_type_var(self) -> None:
        """U should be a TypeVar with no constraints."""
        assert hasattr(U, "__name__")
        assert U.__name__ == "U"
        assert U.__bound__ is None

    def test_f_is_type_var_bound_to_exception(self) -> None:
        """F should be a TypeVar bound to Exception."""
        assert hasattr(F, "__name__")
        assert F.__name__ == "F"
        assert F.__bound__ is Exception

    def test_type_vars_are_exported(self) -> None:
        """All type variables should be accessible from module."""
        from results.core import types

        assert hasattr(types, "T")
        assert hasattr(types, "E")
        assert hasattr(types, "U")
        assert hasattr(types, "F")

    def test_type_vars_in_all(self) -> None:
        """All type variables should be listed in __all__."""
        from results.core import types

        assert "T" in types.__all__
        assert "E" in types.__all__
        assert "U" in types.__all__
        assert "F" in types.__all__
