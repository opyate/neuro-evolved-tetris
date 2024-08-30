# Intro

v3 of Tetris neuro-evolved NNs which uses a client/server model.

Server: will host the thousands of brains, and use multi-threading for crossover and mutation, and keep brains in memory (less IO).
Client: similar to v1/v2 p5/canvas HTML to render simulations, but getting board states through web socket.

As the Tetris engine is not tied to game loops or rendering logic, potentially warm up the bots first with thousands/millions of iterations and check for scoring before we start rendering anything. 

# Run

```
pip install -r requirements.txt
pip3 install torch --index-url https://download.pytorch.org/whl/cu124
```
