"""Helper for generating unique values with Faker."""

from typing import Callable, Set
from faker import Faker


class UniqueValueGenerator:
    """Generate unique values with automatic retry and deduplication."""

    def __init__(self, faker_instance: Faker = None):
        """Initialize unique value generator.

        Args:
            faker_instance: Faker instance to use. If None, creates a new one.
        """
        self.fake = faker_instance or Faker()
        self.used_values: dict[str, Set] = {}

    def generate_unique(
        self,
        generator_func: Callable,
        key: str,
        max_retries: int = 100
    ) -> str:
        """Generate a unique value using the provided generator function.

        Args:
            generator_func: Function that generates a value (e.g., fake.email)
            key: Category key for tracking uniqueness (e.g., 'email', 'phone')
            max_retries: Maximum number of attempts to generate a unique value

        Returns:
            A unique value

        Raises:
            ValueError: If unable to generate unique value after max_retries
        """
        if key not in self.used_values:
            self.used_values[key] = set()

        for attempt in range(max_retries):
            value = generator_func()
            if value not in self.used_values[key]:
                self.used_values[key].add(value)
                return value

        raise ValueError(
            f"Failed to generate unique {key} after {max_retries} attempts. "
            f"Generated {len(self.used_values[key])} unique values so far."
        )

    def generate_unique_email(self) -> str:
        """Generate a unique email address."""
        return self.generate_unique(self.fake.email, 'email')

    def generate_unique_phone(self) -> str:
        """Generate a unique phone number in format XXX-XXX-XXXX."""
        import random
        def phone_gen():
            return f"{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        return self.generate_unique(phone_gen, 'phone')

    def clear(self, key: str = None):
        """Clear tracked values.

        Args:
            key: Specific key to clear. If None, clears all.
        """
        if key:
            self.used_values.pop(key, None)
        else:
            self.used_values.clear()

    def reset(self):
        """Reset all tracked values and Faker's unique state."""
        self.used_values.clear()
        self.fake.unique.clear()
