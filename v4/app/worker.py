import concurrent.futures
import os
import sys
import traceback
from enum import Enum
from itertools import chain
from typing import Dict, List

# from app.tetris_bot import TetrisBot
from app.fake_bot import TetrisBot
from app.worker_util import crossover_with_fittest, weighted_selection
from celery import Celery

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379"
)


class EventType(Enum):
    TICK = "tick"
    MEGATICK = "megatick"


events = [EventType.TICK] * 8 + [EventType.MEGATICK] * 1


@celery.task(name="bots_think_then_move", bind=True)
def bots_think_then_move(self, bots: List[TetrisBot], bot_opts: dict = None):
    if len(bots) == 0:
        return "no_bots"
    # deserialize bots
    bots = [TetrisBot.from_json(bot) for bot in bots]

    try:
        return _bots_think_then_move(self, bots, bot_opts)
    except Exception as e:
        task_id = self.request.id
        print(f"Exception: task={task_id}, exception={e}", flush=True)
        print(traceback.format_exc(), flush=True)
        # self.update_state(state="FAILURE", meta={"error": str(e)})
        raise e


def _bots_think_then_move(self, bots: List[TetrisBot], bot_opts: dict = None):
    if bot_opts is None:
        bot_opts = {}

    loop_count = 0
    while True:
        loop_count += 1

        event_count = 0
        for event in events:
            event_count += 1

            results = process_event(bots, event)

            meta = {
                "count": {
                    "loop": loop_count,
                    "event": event_count,
                },
                "results": results,
            }
            self.update_state(state="PROGRESS", meta=meta)

            # check if all bots are game over
            all_game_over = all(bot.engine.is_game_over for bot in bots)

            if all_game_over:
                meta["all_game_over"] = True
                meta["version"] = 2
                return meta


# Function to handle a chunk of bots' events
def process_event(bots: List[TetrisBot], event: EventType) -> List[tuple[Dict, bool]]:
    do_tick = event == EventType.MEGATICK
    results = []

    for bot in bots:
        moved = bot.think_then_move(do_tick)
        bot_state = bot.to_json()
        # results.append((bot_state, moved))
        results.append(bot_state)

    return results


def when_all_game_over(
    bots: List[TetrisBot],
    executor: concurrent.futures.Executor,
    loop_count: int = 0,
):
    total_fitness = sum(bot.fitness for bot in bots)
    mean_fitness = total_fitness / len(bots)
    min_fitness = min(bot.fitness for bot in bots)
    max_fitness = max(bot.fitness for bot in bots)
    # number of bots with score > 0
    scorer_count = sum(1 for bot in bots if bot.engine.total_score > 0)

    log = f"{loop_count},{scorer_count},{mean_fitness:.2f},{min_fitness:.2f},{max_fitness:.2f}"
    print(
        log,
        flush=True,
    )

    futures = [
        executor.submit(crossover_with_fittest, bot, bots, total_fitness)
        for bot in bots
    ]

    try:
        concurrent.futures.wait(futures)
    except Exception as e:
        print(f"Crossover Exception: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        sys.exit(1)

    for bot in bots:
        bot.reinit()
