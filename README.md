# v1

- run everything in single thread (see tag `v1`)

# v2

- use web workers (see tag `v2`)
- uses a custom ml5 which has support for persisting to IndexedDB: https://github.com/opyate/ml5-next-gen/tree/feature/nn-indexeddb

For many workers, check `about:config` then `dom.workers.maxPerDomain` is at least a few points more than the number of workers you want to spawn.
 
Possibly also max out your soft ulimit to be the same as your hard ulimit:

```
ulimit -Sn $(ulimit -Hn)
```

# TODO

- fewer shared web workers, as more workers aren't necessarily more performant
- client/server model, and have a web server handler brain persistence and state transfer via web sockets

