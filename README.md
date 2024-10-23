# Intro

Neuro-evolutionary bots that learn to play Tetris, by spawning thousands of bots, then doing crossover on weighted selections of nets (virtual coin flip whether a weight comes from parent A or B), then mutation (a small percent chance that any given weight will mutate, mimicking real-world genetic mutations, which typically introduce minor changes rather than entirely new traits).

[Video](https://www.youtube.com/watch?v=Q1aHP5IODUs):

[![Video](https://img.youtube.com/vi/Q1aHP5IODUs/0.jpg)](https://www.youtube.com/watch?v=Q1aHP5IODUs)

# Implementation

Tetris neuro-evolved NNs which uses a worker model.

Server: interface between client and workers
Worker: Docker scaled workers, with light-weight Redis-backed coordinator, and will each run hundreds of brains, and use Redis-backed store for crossover and mutation.
Client: p5/canvas HTML to render simulations, and getting board states through web socket.

# Run

Copy the `.env`:

```
cp .env.example .env
```

Then modify `NUMBER_OF_WORKERS` and `BOTS_PER_WORKER`.

```
docker compose up
```

Then visit

http://127.0.0.1:8000/


# Development setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip3 install torch --index-url https://download.pytorch.org/whl/cu124
```

Got redis.conf from:

```
curl -O https://raw.githubusercontent.com/redis/redis/refs/tags/7.4.0/redis.conf 
```

# Task definition

I am building a neuro-evolutionary simulation of bots learning to play Tetris using Python and PyTorch, which does the following:

- spawn thousands of bots from the simulation runner, and have a bots_list of size N
- the bots are initialised with a zeroed PyTorch network, which has 10x20 inputs, and 6 outputs
- each bot has a state, in the form of a Tetris engine
- the PyTorch network's inputs represent the Tetris grid, and the 6 outputs represent the 6 moves a bot can make: up, down, left, right, rotate_clockwise, rotate_counter_clockwise or noop (which means "make no move", or "no operation")
- the simulation loop now starts, and the runner asks each bot to predict their next move
- after each bot made their move, they get one fitness point for staying alive, and many more fitness points for scoring (i.e. clearing lines on the Tetris grid)
- after each bot made their move, they might also be in a game over state
- after all bots reach game over, the evolution starts
- evolution step 1: parents are chosen based on a weighted selection
- evolution step 2: the parents are crossed-over, to produce a child
- evolution step 3: the child is slightly mutated
- set each bot's next_brain to the new child
- the entire bots_list is re-initialised so their next_brain becomes their current_brain
- the simulation loops

# Future

- https://github.com/joerick/pyinstrument to find slow spots in code
