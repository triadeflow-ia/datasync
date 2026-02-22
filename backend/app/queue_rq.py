# Fila RQ: enfileira processamento de jobs (usado pelo FastAPI)
import os

if os.getenv("TESTING", "").lower() in ("1", "true"):
    # Em modo teste, usa uma fila fake (RQ requer fork, indisponível no Windows)
    class _FakeQueue:
        def enqueue(self, *args, **kwargs):
            pass
    queue = _FakeQueue()
else:
    from redis import Redis
    from rq import Queue
    from app.config import REDIS_URL

    _redis = Redis.from_url(REDIS_URL)
    queue = Queue("default", connection=_redis)
