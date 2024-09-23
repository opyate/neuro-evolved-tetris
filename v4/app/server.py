from app import driver
from celery.result import AsyncResult
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

latest_bot_states = {}
job = None
result = None


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        # https://reqbin.com/req/doog8aai/http-headers-to-prevent-caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


app = FastAPI()
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result,
    }
    return JSONResponse(result)


@app.get("/start")
async def start(n: int = 10):
    print("/start")
    global job

    if job is None:

        bot_opts = {"width": 10, "height": 10}
        job = driver.main(n, bot_opts)

        # Run the group of tasks
        global result
        result = job.apply_async()

        # while not job.ready():
        #     pass

        # if job.successful():
        #     pass
        #     # check game over etc

        # # Optionally, wait for completion and get the results
        # results = result.get()
        # all_game_over = all([result["all_game_over"] for result in results])
        # print("All chunks processed. Combined results:", results)
        # print("All game over?", all_game_over)

        return {"message": f"Started {n} bots"}
    else:
        return {"message": "Already started"}


@app.get("/job")
async def job_state():
    global result
    if result is not None:

        result_get = "no result"
        is_all_game_over = False
        if result.successful():
            # global result
            result_get = result.get()
            is_all_game_over = all([result == "all_game_over" for result in result_get])

        return {
            "message": "Latest job state",
            "ready": result.ready(),
            "successful": result.successful(),
            "failed": result.failed(),
            "waiting": result.waiting(),
            "completed_count": result.completed_count(),
            "is_all_game_over": is_all_game_over,
            "result": result_get,
        }
    else:
        return {"message": "No job started"}


@app.get("/stop")
async def stop():
    print("/stop")

    return {"message": "Stopped all bots"}


@app.get("/state")
async def state():
    return {"message": "Latest bot states", "latest_bot_states": latest_bot_states}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "tick":
                # print("tick")
                await manager.send(latest_bot_states, websocket)
            else:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)


manager = ConnectionManager()
