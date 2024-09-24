import multiprocessing

# from app.tetris_bot import TetrisBot
from app.fake_bot import TetrisBot
from app.worker import bots_next_round, bots_think_then_move
from celery import chord
from celery.result import AsyncResult


def chunkify(lst, n):
    """Splits list into n chunks."""
    return [lst[i::n] for i in range(n)]


def main(bots: list[TetrisBot] | list[dict]):

    # Check if the list contains TetrisBot objects
    if isinstance(bots[0], TetrisBot):
        # if all(isinstance(bot, TetrisBot) for bot in bots):
        # Serialize bots if they are TetrisBot objects
        bots = [bot.to_json() for bot in bots]

    return _main(bots)


def _main(bots) -> AsyncResult:
    num_cores = multiprocessing.cpu_count()

    # return chord(
    #     (
    #         bots_think_then_move.s(bots_slice)
    #         for bots_slice in chunkify(bots, num_cores)
    #     ),
    #     bots_next_round.s(),
    # ).apply_async()

    return chord(
        (bots_think_then_move.s(bots_slice) for bots_slice in chunkify(bots, num_cores))
    )(bots_next_round.s())
