from fastapi import FastAPI

from app.api.routes import chapters, evals, generation, inspirations, projects


def create_app() -> FastAPI:
    app = FastAPI(title="Novel Agent API")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(projects.router)
    app.include_router(chapters.router)
    app.include_router(generation.router)
    app.include_router(inspirations.router)
    app.include_router(evals.router)

    return app


app = create_app()
