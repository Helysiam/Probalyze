import asyncio
import signal
from packages.utils.logger import get_logger
from packages.utils.config import settings
from apps.worker.tasks.ingestion import run_ingestion_cycle
from apps.worker.tasks.compute import run_compute_cycle

logger = get_logger(__name__)

RUNNING = True


def handle_shutdown(sig, frame):
    global RUNNING
    logger.warning(f"Received signal {sig}, shutting down worker...")
    RUNNING = False


async def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    logger.info("Probalyze Worker started.")

    while RUNNING:
        try:
            logger.info("─── Starting ingestion cycle ───")
            await run_ingestion_cycle()

            logger.info("─── Starting compute cycle ───")
            await run_compute_cycle()

            logger.info(f"Cycle complete. Sleeping {settings.WORKER_INTERVAL_SECONDS}s...")
            await asyncio.sleep(settings.WORKER_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"Worker cycle error: {e}", exc_info=True)
            await asyncio.sleep(60)  # backoff on error


if __name__ == "__main__":
    asyncio.run(main())
