from redis import Redis
from rq import Worker, Queue
from app.core.config import get_settings

def main():
    redis_conn = Redis.from_url(get_settings().redis_url)
    queues = [Queue('openadzero-scans', connection=redis_conn), Queue('openadzero-default', connection=redis_conn)]
    Worker(queues, connection=redis_conn).work(with_scheduler=False)

if __name__ == '__main__': main()
