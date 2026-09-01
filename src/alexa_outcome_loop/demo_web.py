from __future__ import annotations

from importlib.resources import files

from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

from .demo_engine import build_demo_timeline


async def home(request) -> FileResponse:  # noqa: ARG001
    page = files("alexa_outcome_loop").joinpath("static/index.html")
    return FileResponse(page)


async def health(request) -> JSONResponse:  # noqa: ARG001
    return JSONResponse({"status": "ok", "surface": "simulated_alexa_plus"})


async def run_demo(request) -> JSONResponse:  # noqa: ARG001
    return JSONResponse(build_demo_timeline())


app = Starlette(
    debug=False,
    routes=[
        Route("/", home),
        Route("/health", health),
        Route("/api/demo/run", run_demo, methods=["POST"]),
    ],
)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
