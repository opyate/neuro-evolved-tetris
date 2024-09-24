import json

import redis
from app.fake_bot import TetrisBot

# maybe? https://redis.io/docs/latest/develop/connect/clients/python/redis-py/#example-indexing-and-querying-json-documents


def db_save(r: redis.Redis, bot: TetrisBot):
    bot_id = bot.id
    bot_json = bot.to_json()
    ser_bot = json.dumps(bot_json)
    return r.set(f"bot:{bot_id}", ser_bot)


def db_load(r: redis.Redis, bot_id: int) -> TetrisBot:
    deser_bot = TetrisBot.from_json(json.loads(r.get(f"bot:{bot_id}")))
    return deser_bot


def db_save_all(r: redis.Redis, bots: list[TetrisBot]):
    with r.pipeline() as pipe:
        pipe.multi()
        for bot in bots:
            db_save(pipe, bot)
        return all(pipe.execute())


def db_save_all_dict(r: redis.Redis, bots: list[dict]):
    with r.pipeline() as pipe:
        pipe.multi()
        for bot in bots:
            bot_id = bot["id"]
            ser_bot = json.dumps(bot)
            pipe.set(f"bot:{bot_id}", ser_bot)
        return all(pipe.execute())


def db_load_all(r: redis.Redis, bot_ids: list[int]) -> list[TetrisBot]:
    with r.pipeline() as pipe:
        pipe.multi()
        for bot_id in bot_ids:
            pipe.get(f"bot:{bot_id}")
        serialized_bots = pipe.execute()
    bots = [
        TetrisBot.from_json(json.loads(bot_data))
        for bot_data in serialized_bots
        if bot_data is not None
    ]
    return bots


def db_load_all_dicts(r: redis.Redis, bot_ids: list[int]) -> list[dict]:
    with r.pipeline() as pipe:
        pipe.multi()
        for bot_id in bot_ids:
            pipe.get(f"bot:{bot_id}")
        serialized_bots = pipe.execute()
    bots = [
        json.loads(bot_data) for bot_data in serialized_bots if bot_data is not None
    ]
    return bots
