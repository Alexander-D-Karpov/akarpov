from celery import shared_task


@shared_task()
def run_pipe_thread(pk: int):
    return pk
