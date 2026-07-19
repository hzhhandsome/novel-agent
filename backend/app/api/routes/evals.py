from fastapi import APIRouter

from app.evals.run import run_builtin_evals

router = APIRouter(prefix="/api/evals", tags=["evals"])


@router.get("/builtin")
def get_builtin_eval_report() -> dict:
    return run_builtin_evals()
