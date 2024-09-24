import concurrent.futures
import os
import sys
import time
import traceback
import urllib.request
from enum import Enum
from multiprocessing import process

import redis
from app.db import db_save_all_dict
from app.tetris_bot import TetrisBot
from app.tetris_engine import TetrisEngine
from app.worker_util import crossover_with_fittest
from celery import Celery

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379"
)
celery.conf.result_expires = 60 * 5  # 5 minutes
celery.conf.event_serializer = "pickle"  # this event_serializer is optional. somehow i missed this when writing this solution and it still worked without.
celery.conf.task_serializer = "pickle"
celery.conf.result_serializer = "pickle"
# celery.conf.accept_content = ["application/x-python-serialize", "pickle"]
celery.conf.accept_content = ["pickle"]


r = redis.Redis(host="redis", port=6379, db=0)


class EventType(Enum):
    TICK = "tick"
    MEGATICK = "megatick"


events = [EventType.TICK] * 8 + [EventType.MEGATICK] * 1


@celery.task(name="bots_next_round", bind=True)
def bots_next_round(self, results):

    bot_dicts = [bot for results_chunk in results for bot in results_chunk["bots_dict"]]

    # crossover and mutation, re-init, before saving to Redis
    bots = [TetrisBot.from_dict(bot) for bot in bot_dicts]

    total_fitness = sum(bot.fitness for bot in bots)
    # mean_fitness = total_fitness / len(bots)
    # min_fitness = min(bot.fitness for bot in bots)
    # max_fitness = max(bot.fitness for bot in bots)
    # # number of bots with score > 0
    # scorer_count = sum(1 for bot in bots if bot.engine.total_score > 0)

    # log = f"{scorer_count},{mean_fitness:.2f},{min_fitness:.2f},{max_fitness:.2f}"
    # print(
    #     log,
    #     flush=True,
    # )

    for bot in bots:
        crossover_with_fittest(bot, bots, total_fitness)
    for bot in bots:
        bot.reinit()

    bot_dicts = [bot.to_dict(lite=False) for bot in bots]

    # bot_id_0 = [bot for bot in bot_dicts if bot["id"] == 0]
    # print(
    #     f">bots_next_round: {bot_id_0}",
    #     flush=True,
    # )

    db_result = db_save_all_dict(r, bot_dicts)
    if not db_result:
        raise Exception("Failed to save bots to Redis")

    print(f"worker pinging server to start next round", flush=True)
    urllib.request.urlopen(
        f"http://web:8000/start?n={len(bot_dicts)}&f={self.request.id}"
    ).read()

    # TODO change this to the newly-initialised bots
    return results


@celery.task(name="bots_think_then_move", bind=True)
def bots_think_then_move(self, bots: list[TetrisBot]):
    if len(bots) == 0:
        return "no_bots"
    # deserialize bots
    bots = [TetrisBot.from_dict(bot) for bot in bots]

    try:
        return _bots_think_then_move(self, bots)
    except Exception as e:
        task_id = self.request.id
        print(f"Exception: task={task_id}, exception={e}", flush=True)
        print(traceback.format_exc(), flush=True)
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise e


def _bots_think_then_move(self, bots: list[TetrisBot]):

    # even thought TetrisEngine has to_dict/from_dict, that's only used for rendering, and
    # we know we'll always need a fresh engine at this point
    for bot in bots:
        bot.engine = TetrisEngine(bot.width, bot.height)

    loop_count = 0
    while True:
        loop_count += 1

        event_count = 0
        for event in events:
            event_count += 1

            process_event(bots, event)
            time.sleep(1.0)

            # update_state is not useful for our use-case, so we use redis directly instead
            # self.update_state(state="PROGRESS", meta=meta)
            db_result = db_save_all_dict(
                r, [bot.to_dict(lite=True) for bot in bots], "render_bot"
            )
            if not db_result:
                raise Exception("Failed to save render_bots to Redis")

            # check if all bots are game over
            all_game_over = all(bot.engine.is_game_over for bot in bots)

            if all_game_over:
                bot_id_0 = [bot for bot in bots if bot.id == 0]
                if bot_id_0:
                    print(f">all_game_over: {bot_id_0}", flush=True)

                return {
                    "count": {
                        "loop": loop_count,
                        "event": event_count,
                    },
                    "bots_dict": [bot.to_dict(lite=False) for bot in bots],
                }


def process_event(bots: list[TetrisBot], event: EventType):
    """For each bot, think and move based on the event.

    Returns nothing, as the bots are mutated in place.
    """
    do_tick = event == EventType.MEGATICK

    for bot in bots:
        if bot.id == 0:
            print(f">bot_before: {bot}", flush=True)
        bot.think_then_move(do_tick)
        if bot.id == 0:
            print(f">bot_after: {bot}", flush=True)
