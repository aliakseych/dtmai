import importlib

from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker

from app.bootstrap.registry import TASK_MODULES
from app.settings import get_settings

# redis-py 8 defaults socket_timeout to 5s, which kills the worker's indefinite BRPOP.
broker = ListQueueBroker(get_settings().redis_url, socket_timeout=None)
scheduler = TaskiqScheduler(broker, [LabelScheduleSource(broker)])

for _module in TASK_MODULES:
    importlib.import_module(_module)
