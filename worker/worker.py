import multiprocessing
from redis import Redis
from rq import Worker, Queue

# Windows fix
multiprocessing.set_start_method("spawn", force=True)

redis_conn = Redis()
queue = Queue(connection=redis_conn)

def process_submission(submission_id):
    print("Processing submission:", submission_id)

if __name__ == "__main__":
    worker = Worker([queue], connection=redis_conn)
    worker.work()