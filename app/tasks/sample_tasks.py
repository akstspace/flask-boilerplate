
from app.celery import celery


@celery.task(name="app.tasks.add_numbers")
def add_numbers(x, y):
    """
    Sample Celery task: Add two numbers

    Usage:
        from app.tasks import add_numbers
        result = add_numbers.delay(4, 6)
        result.get()  # Returns 10
    """
    return x + y
