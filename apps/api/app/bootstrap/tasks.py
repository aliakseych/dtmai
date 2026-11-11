import importlib

from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker

from app.bootstrap.registry import TASK_MODULES
from app.settings import get_settings

broker = ListQueueBroker(get_settings().redis_url)
scheduler = TaskiqScheduler(broker, [LabelScheduleSource(broker)])

for _module in TASK_MODULES:
    importlib.import_module(_module)
