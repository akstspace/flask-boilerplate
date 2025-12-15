"""Unit tests for Celery tasks"""

from app.tasks.sample_tasks import add_numbers


class TestCeleryTasks:
    """Tests for Celery tasks"""

    def test_add_numbers(self):
        """Test add_numbers task"""
        result = add_numbers(5, 10)
        assert result == 15

    def test_add_numbers_negative(self):
        """Test add_numbers with negative numbers"""
        result = add_numbers(-5, 10)
        assert result == 5

    def test_add_numbers_zero(self):
        """Test add_numbers with zero"""
        result = add_numbers(0, 0)
        assert result == 0

