from celery import current_app as current_celery_app
from celery.result import AsyncResult

from project.config import settings


def create_celery():
    celery_app = current_celery_app
    celery_app.config_from_object(settings, namespace="CELERY")

    return celery_app


def get_task_info(task_id: str):
    """
    return task info according to the task_id
    """
    task = AsyncResult(task_id)
    if task.state == "FAILURE":
        response = {
            "state": task.state,
            "error": str(task.result),
        }
    else:
        response = {
            "state": task.state,
        }
    return response
