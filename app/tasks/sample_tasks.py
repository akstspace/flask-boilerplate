from app.celery import celery


@celery.task(name="app.tasks.add_numbers")
def add_numbers(x, y):
    """
    Compute the sum of two numbers.
    
    Parameters:
        x (number): First addend.
        y (number): Second addend.
    
    Returns:
        number: The sum of `x` and `y`.
    """
    return x + y