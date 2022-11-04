import logging
import random

import requests
from celery.result import AsyncResult
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from project.database import get_db_session

from . import users_router
from .models import User
from .schemas import UserBody
from .tasks import (
    sample_task,
    task_add_subscribe,
    task_process_notification,
    task_send_welcome_email,
)
from .utils import random_username


logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="project/users/templates")


# + Problem 1: Blocking Web Process


@users_router.get("/form/")
def form_example_get(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@users_router.post("/form/")
def form_example_post(user_body: UserBody):
    task = sample_task.delay(user_body.email)
    return JSONResponse({"task_id": task.task_id})


@users_router.get("/task_status/")
def task_status(task_id: str):
    task = AsyncResult(task_id)
    if task.state == "FAILURE":
        response = {"state": task.state, "error": str(task.result)}
    else:
        response = {"state": task.state}
    return JSONResponse(response)


# - Problem 1: Blocking Web Process


# + Problem 2: Webhook Handler


@users_router.post("/webhook_test_bad/")
def webhook_test_bad():
    """
    При таком запросе процесс gunicorn будет заблокирован на 5 сек.
    Для решения проблемы долгие операции лучше делать через celery
    """
    if not random.choice([0, 1]):
        # mimic an error
        raise Exception()

    # blocking process
    requests.post("https://httpbin.org/delay/5")
    return "pong"


@users_router.post("/webhook_test_good/")
def webhook_test_good():
    task = task_process_notification.delay()
    print(task.id)
    return "pong"


# - Problem 2: Webhook Handler


# + Web-sockets example


@users_router.get("/form_ws/")
def form_ws_example(request: Request):
    return templates.TemplateResponse("form_ws.html", {"request": request})


# - Web-sockets example


# + Socket.io example


@users_router.get("/form_socketio/")
def form_socketio_example(request: Request):
    return templates.TemplateResponse("form_socketio.html", {"request": request})


# - Socket.io example


# + database transactions example


@users_router.get("/transaction_celery/")
def transaction_celery(session: Session = Depends(get_db_session)):
    try:
        username = random_username()
        user = User(
            username=f"{username}",
            email=f"{username}@test.com",
        )
        session.add(user)
        session.commit()
    except Exception:
        session.rollback()
        raise

    # + Logging example
    # print(f'user {user.id} {user.username} is persistent now')
    logger.info(f"user {user.id} {user.username} is persistent now")
    # - Logging example

    task_send_welcome_email.delay(user.id)
    return {"message": "done"}


# - database transactions example


# + pytest example


@users_router.post("/user_subscribe/")
def user_subscribe(user_body: UserBody, session: Session = Depends(get_db_session)):
    try:
        user = session.query(User).filter_by(username=user_body.username).first()
        if user:
            user_id = user.id
        else:
            user = User(
                username=user_body.username,
                email=user_body.email,
            )
            session.add(user)
            session.commit()
            user_id = user.id
    except Exception:
        session.rollback()
        raise

    task_add_subscribe.delay(user_id)
    return {"message": "send task to Celery successfully"}


# - pytest example
