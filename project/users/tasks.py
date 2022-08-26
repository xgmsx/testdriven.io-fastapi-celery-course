import random
import logging
from logging.handlers import WatchedFileHandler

import requests
from asgiref.sync import async_to_sync
from celery import shared_task, Task
from celery.signals import task_postrun, after_setup_logger
from celery.utils.log import get_task_logger

from project.database import db_context

logger = get_task_logger(__name__)


@shared_task
def divide(x, y):
    # from celery.contrib import rdb
    # rdb.set_trace()
    import time
    time.sleep(5)
    return x / y


@task_postrun.connect
def task_postrun_handler(task_id, **kwargs):
    # + Web-sockets example
    from project.ws.views import update_celery_task_status
    async_to_sync(update_celery_task_status)(task_id)
    # - Web-sockets example
    # + Socket.io example
    from project.ws.views import update_celery_task_status_socketio  # new
    update_celery_task_status_socketio(task_id)
    # - Socket.io example


# + Logging example

# @after_setup_logger.connect()
# def on_after_setup_logger(logger, **kwargs):
#     formatter = logger.handlers[0].formatter
#     # file_handler = logging.FileHandler('celery.log')
#     file_handler = logging.handlers.TimedRotatingFileHandler('celery_tasks.log', 'midnight', 1)
#     file_handler.setFormatter(formatter)
#     logger.addHandler(file_handler)


@shared_task()
def task_test_logger():
    logger.info("test")

# - Logging example


# + Problem 1: Blocking Web Process

@shared_task
def sample_task(email):
    # used for testing a failed api call
    if random.choice([0, 1]):
        raise Exception("random processing error")

    # used for simulating a call to a third-party api
    requests.post("https://httpbin.org/delay/5")


# - Problem 1: Blocking Web Process


# + Problem 2: Webhook Handler

@shared_task(bind=True)
def task_process_notification_old(self):
    try:
        if not random.choice([0, 1]):
            # mimic random error
            raise Exception()

        # this would block the I/O
        requests.post("https://httpbin.org/delay/5")
    except Exception as e:
        logger.error("exception raised, it would be retry after 5 seconds")
        raise self.retry(exc=e, countdown=5)

# - Problem 2: Webhook Handler


# + Retrying failed task

@shared_task(bind=True, autoretry_for=(Exception,),
             retry_backoff=5, retry_jitter=True,
             retry_kwargs={"max_retries": 5})
def task_process_notification(self):
    if not random.choice([0, 1]):
        # mimic random error
        raise Exception()

    # this would block the I/O
    requests.post("https://httpbin.org/delay/5")


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception, KeyError)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True
    retry_jitter = True


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_process_notification_base_class(self):
    raise Exception()


# + Retrying failed task


# + Celery Beat example

@shared_task(name="task_schedule_work")
def task_schedule_work():
    logger.info("task_schedule_work run")

# - Celery Beat example


# + Celery routing example

# dynamic routing:

@shared_task(name="default:dynamic_example_one")
def dynamic_example_one():
    logger.info("Example One")


@shared_task(name="low_priority:dynamic_example_two")
def dynamic_example_two():
    logger.info("Example Two")


@shared_task(name="high_priority:dynamic_example_three")
def dynamic_example_three():
    logger.info("Example Three")

# - Celery routing example


# + database transactions example

@shared_task()
def task_send_welcome_email(user_pk):
    from project.users.models import User

    with db_context() as session:
        user = session.query(User).get(user_pk)
        logger.info(f'send email to {user.email} {user.id}')

# - database transactions example


# + pytest example

@shared_task(bind=True)
def task_add_subscribe(self, user_pk):
    with db_context() as session:
        try:
            from project.users.models import User
            user = session.query(User).get(user_pk)
            requests.post(
                "https://httpbin.org/delay/5",
                data={"email": user.email},
            )
        except Exception as exc:
            raise self.retry(exc=exc)

# - pytest example
