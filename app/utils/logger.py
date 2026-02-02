import logging
import json
import os
import uuid
from logging.handlers import RotatingFileHandler
from flask import request, has_request_context, session
from datetime import datetime
import traceback

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings for log records.
    Fields: timestamp, level, message, module, function, line, request_id, user_id, path, ip
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }

        # Add Request Context if available
        if has_request_context():
            log_record["request_id"] = getattr(request, "request_id", "unknown")
            log_record["ip"] = request.remote_addr
            log_record["method"] = request.method
            log_record["path"] = request.path
            log_record["user_agent"] = request.user_agent.string
            
            # User Context (if logged in)
            log_record["user_id"] = session.get('user_id', 'anonymous')
            log_record["user_role"] = session.get('role', 'unknown')
        else:
            log_record["context"] = "system/background"

        # Stack Trace for Exceptions
        if record.exc_info:
            log_record["exception"] = record.exc_info[0].__name__
            log_record["stack_trace"] = traceback.format_exception(*record.exc_info)

        return json.dumps(log_record)

def setup_logging(app):
    """
    Configures the application logger with RotatingFileHandler and JSONFormatter
    """
    # 1. Create logs directory
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')

    # 2. Configure Handler (Rotate at 10MB, keep 5 backups)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.INFO)

    # 3. Attach to App Logger
    # Remove default handlers to avoid duplicate/non-JSON logs
    del app.logger.handlers[:]
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # 4. Silence Chatty Libraries (Optional)
    logging.getLogger('werkzeug').setLevel(logging.WARNING) # Reduce Flask dev server noise in production logs if needed

    app.logger.info("✅ Enterprise Logging Initialized")
