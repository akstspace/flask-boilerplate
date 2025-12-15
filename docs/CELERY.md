# Celery Guide

This boilerplate includes **Celery** for asynchronous task processing with **Redis** as the message broker.

## Overview

Celery allows you to:
- Run long-running tasks asynchronously
- Schedule periodic tasks
- Process tasks across multiple workers
- Retry failed tasks automatically

## Technology Stack

- **Celery 5.6**: Task queue framework
- **Redis**: Message broker and result backend
- **kombu**: AMQP library for task serialization

## Configuration

Celery is configured in `app/celery/celery_config.py`:

```python
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
```

Configuration is managed through environment variables:

```dotenv
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Starting Redis

Redis must be running for Celery to work.

### Docker

```bash
docker run --name redis -p 6379:6379 -d redis
```

### Docker Compose

```bash
docker-compose up -d
```

### Local Installation (macOS)

```bash
brew install redis
brew services start redis
```

## Creating Tasks

Tasks are defined in `app/tasks/`. Create a new file for related tasks:

```python
# app/tasks/email_tasks.py
from app.celery import celery
from flask import current_app
from loguru import logger

@celery.task(name='app.tasks.send_email')
def send_email(recipient, subject, body):
    """Send email asynchronously"""
    logger.info(f"Sending email to {recipient}")
    
    # Your email logic here
    # e.g., using smtp
    
    return f"Email sent to {recipient}"

@celery.task(name='app.tasks.process_data', bind=True, max_retries=3)
def process_data(self, data):
    """Process data with automatic retry"""
    try:
        # Process data
        result = expensive_operation(data)
        return result
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        # Retry in 60 seconds, up to 3 times
        raise self.retry(exc=exc, countdown=60)
```

### Task Registration

Tasks are auto-discovered in `app/celery/celery_config.py`:

```python
celery.autodiscover_tasks(["app.tasks"])
```

Any task decorated with `@celery.task` in `app/tasks/` is automatically available.

## Starting the Celery Worker

Run the worker in a separate terminal:

```bash
celery -A app.celery worker --loglevel=info
```

You should see:

```
celery@hostname ready to accept tasks
```

## Running Tasks

### Fire and Forget (Async)

Execute immediately without waiting for results:

```python
from app.tasks.email_tasks import send_email

# Task runs asynchronously
send_email.delay('user@example.com', 'Welcome', 'Hello!')
```

### With Result Tracking

```python
result = send_email.delay('user@example.com', 'Welcome', 'Hello!')

# Later, check if task is done
if result.ready():
    print(result.get())  # Returns task result
else:
    print("Task still processing...")
```

### Calling from Flask Routes

```python
from flask_restx import Namespace, Resource
from app.tasks.email_tasks import send_email

@users_ns.route('/send-welcome')
class SendWelcome(Resource):
    def post(self):
        email = request.json.get('email')
        task = send_email.delay(email, 'Welcome!', 'Thanks for signing up')
        return {'task_id': task.id, 'status': 'queued'}, 202
```

## Task Examples

### Simple Task

```python
@celery.task(name='app.tasks.add_numbers')
def add_numbers(x, y):
    """Add two numbers"""
    return x + y

# Usage
result = add_numbers.delay(4, 6)
print(result.get())  # Returns 10
```

### Task with Flask App Context

```python
@celery.task(name='app.tasks.send_notification')
def send_notification(user_id, message):
    """Send notification to user"""
    from flask import current_app
    from app.models.user import User
    
    with current_app.app_context():
        user = User.query.get(user_id)
        if user:
            # Send notification logic
            logger.info(f"Notified {user.email}: {message}")
```

### Chaining Tasks

```python
from celery import chain, group

# Run tasks sequentially
workflow = chain(
    task1.s(10),
    task2.s(5),
    task3.s()
)
result = workflow.apply_async()

# Run tasks in parallel
parallel_tasks = group([
    task1.s(1),
    task2.s(2),
    task3.s(3)
])
results = parallel_tasks.apply_async()
```

### Periodic/Scheduled Tasks

```python
from celery.schedules import crontab

# In celery configuration
celery.conf.beat_schedule = {
    'send-reminders-every-hour': {
        'task': 'app.tasks.send_reminders',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

Start the Celery Beat scheduler:

```bash
celery -A app.celery beat --loglevel=info
```

## Task Monitoring

### Using Flower (Web UI)

Install Flower:

```bash
pip install flower
```

Start Flower:

```bash
flower -A app.celery --port=5555
```

Visit `http://localhost:5555` to monitor tasks, workers, and queues.

### Command Line

```bash
# Show active tasks
celery -A app.celery inspect active

# Show registered tasks
celery -A app.celery inspect registered

# Show worker stats
celery -A app.celery inspect stats
```

## Task Configuration

### Retry on Failure

```python
@celery.task(bind=True, autoretry_for=(Exception,), max_retries=3, default_retry_delay=60)
def unreliable_task(self):
    """Automatically retry on exception"""
    # Task logic
    pass
```

### Time Limits

```python
@celery.task(time_limit=300, soft_time_limit=280)
def long_running_task():
    """Hard limit: 5 minutes, soft limit: 4m 40s"""
    # Task logic
    pass
```

### Task Routing

Route tasks to specific workers:

```python
@celery.task(queue='email', routing_key='email.send')
def send_email(recipient, subject):
    pass

# Start worker for email queue only
celery -A app.celery worker -Q email --loglevel=info
```

## Example Use Cases

### 1. Sending Emails

```python
@celery.task
def send_email(recipient, subject, body):
    import smtplib
    # Email sending logic
    pass

# In route
send_email.delay(user.email, 'Welcome', 'Hello!')
```

### 2. Generating Reports

```python
@celery.task(bind=True)
def generate_report(self, report_id):
    from app.models.report import Report
    with current_app.app_context():
        report = Report.query.get(report_id)
        report.status = 'processing'
        db.session.commit()
        
        # Generate report
        data = expensive_calculation()
        
        report.status = 'completed'
        report.data = data
        db.session.commit()
    return report_id
```

### 3. Data Processing

```python
@celery.task
def process_large_csv(file_path):
    import pandas as pd
    df = pd.read_csv(file_path)
    # Process data
    return df.to_json()
```

## Troubleshooting

### Task not executing

1. Ensure Redis is running: `redis-cli ping`
2. Check Celery worker is running: `celery -A app.celery worker`
3. Verify task is registered: `celery -A app.celery inspect registered`

### Worker crashes

Check logs in `logs/` or run worker with verbose logging:

```bash
celery -A app.celery worker --loglevel=debug
```

### Tasks stuck in queue

Clear the queue:

```bash
celery -A app.celery purge  # CAUTION: Deletes all tasks
```

### Connection to broker failed

```
Error: Unable to connect to broker
```

Check:
1. Redis is running and accessible
2. `CELERY_BROKER_URL` is correct
3. Network connectivity (if Redis is remote)

## Testing Celery Tasks

See [TESTING.md](TESTING.md) for testing Celery tasks with mocks.

## Next Steps

- Review [DATABASE.md](DATABASE.md) for database operations in tasks
- See [TESTING.md](TESTING.md) for testing async tasks
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for running Celery in production
