import os
import time

from project.database import SessionLocal
from project.users.models import User

from alembic.config import Config
from alembic import command


def create_user(username: str, email: str):
    user = User(username=username, email=email)
    session = SessionLocal()
    if not session.query(User).first():
        session.add(user)
        session.commit()
        print(f"User '{username}' created")
    else:
        print(f"User '{username}' already exists")


def create_db():
    migrate_db(True)
    print("Database created")


def migrate_db(create: bool = False):
    project_dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(project_dir_path, "alembic.ini")
    alembic_cfg = Config(file_=config_path)
    command.upgrade(alembic_cfg, "head")
    if not create:
        print("Database migrated")


def run_demo_task(a=1, b=2):
    from main import app  # noqa
    from project.users.tasks import divide
    print(f"Running celery demo task \"divide({a}, {b})\"")
    task = divide.delay(a, b)
    for num, _ in enumerate(range(5), start=1):
        time.sleep(1)
        print(num, f"state={task.state}, result={task.result}",)
    return task


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, debug=True)
