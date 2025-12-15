import multiprocessing
import os

# Server socket
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "2"))

# Process naming
proc_name = "flask_app"

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Server mechanics
daemon = False
pidfile = None
# Note: user/group/umask are set to None/0 assuming the container/orchestrator
# enforces a non-root user via Dockerfile USER directive or pod security context.
# For production hardening, consider:
# - Running container as non-root user (USER directive in Dockerfile)
# - Setting umask to 0o022 or 0o027 if file permissions need tightening
# - Using pod security policies/contexts in Kubernetes for additional enforcement
umask = 0
user = None
group = None
tmp_upload_dir = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance tuning
max_requests = 1000
max_requests_jitter = 50

# Graceful timeout for workers
graceful_timeout = 30


# =======
# optional
# =======


# SSL (uncomment and configure if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Pre/post fork hooks (optional)
# def on_starting(server):
#     """Called just before the master process is initialized."""
#     pass

# def on_reload(server):
#     """Called to recycle workers during a reload via SIGHUP."""
#     pass

# def when_ready(server):
#     """Called just after the server is started."""
#     pass

# def pre_fork(server, worker):
#     """Called just before a worker is forked."""
#     pass

# def post_fork(server, worker):
#     """Called just after a worker has been forked."""
#     pass

# def post_worker_init(worker):
#     """Called just after a worker has initialized the application."""
#     pass

# def worker_exit(server, worker):
#     """Called just after a worker has been exited."""
#     pass