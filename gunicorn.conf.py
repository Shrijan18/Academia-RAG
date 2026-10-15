import os

# Port assigned by Render / Railway or default to 10000
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"
workers = 1
worker_class = "sync"
timeout = 300
keepalive = 5
accesslog = "-"
errorlog = "-"
