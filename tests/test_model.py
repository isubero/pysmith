import pytest
from pydantic import ValidationError

from pysmith.models import Model


class User(Model):
    """Test model for User."""

    id: int
    name: str
    age: int


class TestModelTypeValidation:
    """Test type validation in Model class."""

    def test_correct_types(self):
        """Test that Model correctly accepts valid types."""
        user = User(id=123, name="John Doe", age=30)

        assert user.id == 123
        assert user.name == "John Doe"
        assert user.age == 30
        assert isinstance(user.id, int)
        assert isinstance(user.name, str)
        assert isinstance(user.age, int)

    def test_incorrect_type_raises_error(self):
        """Test that Model raises ValidationError for incorrect types."""
        with pytest.raises(ValidationError) as exc_info:
            User(id="not_a_number", name="Jane Doe", age=25)

        # Pydantic ValidationError contains information about failures
        assert exc_info.value.error_count() > 0
        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("id",)
        assert errors[0]["type"] == "int_parsing"

    def test_multiple_incorrect_types(self):
        """Test that incorrect types raise ValidationError."""
        # age should be int, but Pydantic will coerce "25" to 25
        # Let's test with a truly invalid type that can't be coerced
        with pytest.raises(ValidationError) as exc_info:
            User(id=789, name="Bob Smith", age="not_a_number")

        # Pydantic ValidationError contains information about failures
        assert exc_info.value.error_count() > 0
        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("age",)
        assert errors[0]["type"] == "int_parsing"


class TestModelJsonValidation:
    """Test JSON validation in Model class."""

    def test_validate_json_with_correct_data(self):
        """Test that validate_json correctly parses valid JSON."""
        json_data = '{"id": 123, "name": "Alice Cooper", "age": 28}'
        user = User.validate_json(json_data)

        assert isinstance(user, User)
        assert user.id == 123
        assert user.name == "Alice Cooper"
        assert user.age == 28

    def test_validate_json_with_type_coercion(self):
        """Test that validate_json coerces compatible types."""
        # Pydantic can coerce string "123" to int 123
        json_data = '{"id": "123", "name": "Bob Dylan", "age": 30}'
        user = User.validate_json(json_data)

        assert isinstance(user, User)
        assert user.id == 123
        assert isinstance(user.id, int)
        assert user.name == "Bob Dylan"
        assert user.age == 30

    def test_validate_json_with_invalid_data(self):
        """Test that validate_json raises ValidationError for invalid JSON."""
        # Missing required field
        json_data = '{"id": 123, "name": "Charlie Brown"}'

        with pytest.raises(ValidationError) as exc_info:
            User.validate_json(json_data)

        # Verify that the error is about the missing 'age' field
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("age",) for error in errors)

    def test_pydantic_model_creation(self):
        """Test that pydantic model class is correctly created."""
        # Use the class method to get the Pydantic model class
        pyd_model_cls = User.get_pydantic_model_cls()

        assert pyd_model_cls is not None
        assert pyd_model_cls.__name__ == "User"
        # Verify the model has the expected fields
        assert "id" in pyd_model_cls.model_fields
        assert "name" in pyd_model_cls.model_fields
        assert "age" in pyd_model_cls.model_fields
