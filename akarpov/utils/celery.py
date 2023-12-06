from config.celery_app import app


def get_scheduled_tasks_name() -> list[str]:
    i = app.control.inspect()
    t = i.scheduled()
    all_tasks = []
    for worker, tasks in t.items():
        all_tasks += tasks
    return [x["request"]["name"] for x in all_tasks]
