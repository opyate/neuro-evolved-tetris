import concurrent.futures
import threading
import asyncio
from typing import List, Dict
from app.tetris_bot import TetrisBot
from itertools import chain
import os
import random
from enum import Enum
import traceback

cpu_count = os.cpu_count()


class EventType(Enum):
    TICK = "tick"
    MEGATICK = "megatick"


# Shared stop event
stop_event = asyncio.Event()


# Function to handle each bot's event
def handle_bot_event(bot: TetrisBot, event: EventType) -> tuple[Dict, bool]:
    do_tick = event == EventType.MEGATICK
    moved = bot.think_then_move(do_tick)

    # Return the bot's state after processing the event
    _bot_state = bot.get_state()
    bot_state = {
        **_bot_state,
        "engine": _bot_state["engine"].to_dict(),
    }
    return bot_state, moved


def crossover_with_fittest(bot, bots, total_fitness):
    parent_a_index = weighted_selection(bots, total_fitness)
    parent_b_index = weighted_selection(bots, total_fitness)

    parent_a = bots[parent_a_index]
    parent_b = bots[parent_b_index]

    # Crossover the two parents to produce a new child brain
    bot.crossover(parent_a, parent_b)
    return parent_a_index, parent_b_index


def process_events(
    bots: List[TetrisBot],
    events: List[EventType],
    state_queue: asyncio.Queue,
    executor: concurrent.futures.ThreadPoolExecutor,
):
    all_game_over = True
    updated_bot_states = []

    # Dispatch all events for all bots concurrently
    futures = [
        executor.submit(handle_bot_event, bot, event)
        for bot in bots
        for event in events
    ]

    # Gather all results and aggregate
    for future in concurrent.futures.as_completed(futures):
        bot_state, moved = future.result()
        all_game_over = all_game_over and not moved
        updated_bot_states.append(bot_state)

    if all_game_over:
        total_fitness = sum(bot.fitness for bot in bots)

        futures = [
            executor.submit(crossover_with_fittest, bot, bots, total_fitness)
            for bot in bots
        ]

        for future in concurrent.futures.as_completed(futures):
            parent_a_index, parent_b_index = future.result()

        for bot in bots:
            bot.reinit()

    # Put the updated states in the queue for the main loop to consume
    asyncio.run_coroutine_threadsafe(
        state_queue.put(updated_bot_states), asyncio.get_running_loop()
    )


def process_event(
    bots: List[TetrisBot],
    event: EventType,
    state_queue: asyncio.Queue,
    executor: concurrent.futures.ThreadPoolExecutor,
):
    all_game_over = True
    updated_bot_states = []

    # Dispatch the event to all bots concurrently
    futures = [executor.submit(handle_bot_event, bot, event) for bot in bots]

    # Gather all results and aggregate
    for future in concurrent.futures.as_completed(futures):
        bot_state, moved = future.result()
        all_game_over = all_game_over and not moved
        updated_bot_states.append(bot_state)

    if all_game_over:
        total_fitness = sum(bot.fitness for bot in bots)
        print(f"all dead, total_fitness={total_fitness}", flush=True)

        crossover_futures = [
            executor.submit(crossover_with_fittest, bot, bots, total_fitness)
            for bot in bots
        ]

        for future in concurrent.futures.as_completed(crossover_futures):
            try:
                parent_a_index, parent_b_index = future.result()
                # print(
                #     f"parent_a_index={parent_a_index}, parent_b_index={parent_b_index}",
                #     flush=True,
                # )
            except Exception as e:
                print(f"Crossover Exception: {e}", flush=True)
                print(traceback.format_exc(), flush=True)

        for bot in bots:
            bot.reinit()

    # Put the updated states in the queue for the main loop to consume
    asyncio.run_coroutine_threadsafe(
        state_queue.put(updated_bot_states), asyncio.get_running_loop()
    )


def weighted_selection(bots, total_fitness):
    index = 0
    start = random.uniform(0, 1)  # Random start point between 0 and 1

    while start > 0:
        normalised_fitness = bots[index].fitness / total_fitness
        start -= normalised_fitness
        index += 1

    index -= 1  # Adjust index because we incremented it at the end of the loop

    return index


async def run_bots_continuous(n: int, latest_states: Dict, bot_opts: dict = None):
    stop_event.clear()

    if bot_opts is None:
        bot_opts = {}

    bots = [TetrisBot(i, **bot_opts) for i in range(n)]

    # Create a queue to safely update latest_states
    state_queue = asyncio.Queue()

    # Create the thread pool once

    loop_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count - 1) as executor:
        while not stop_event.is_set():
            # 8 "tick" events followed by 1 "megatick"
            events = list(
                chain.from_iterable([[EventType.TICK] * 8, [EventType.MEGATICK] * 1])
            )
            event_count = 0
            for event in events:
                process_event(bots, event, state_queue, executor)

                # Get updated states from the queue and update latest_states
                updated_bot_states = await state_queue.get()
                # print(f"len of updated_bot_states: {len(updated_bot_states)}")
                latest_states["bots"] = updated_bot_states
                latest_states["event_count"] = event_count
                latest_states["loop_count"] = loop_count
                event_count += 1

            loop_count += 1
            # Control the simulation speed (for example, 60 ticks per second)
            # await asyncio.sleep(1 / 60)


async def stop_bots():
    stop_event.set()
