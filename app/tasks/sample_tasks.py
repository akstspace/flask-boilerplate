from app.celery import celery


@celery.task(name="app.tasks.add_numbers")
def add_numbers(x, y):
    """
    Add two numbers.
    
    Returns:
        sum: The arithmetic sum of `x` and `y`.
    """
    return x + y