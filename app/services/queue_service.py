from redis import Redis
from rq import Queue
from worker.worker import process_submission

redis_conn = Redis()

queue = Queue(connection=redis_conn)

def enqueue_submission(submission_id):

    job = queue.enqueue(process_submission, submission_id)

    return job.id