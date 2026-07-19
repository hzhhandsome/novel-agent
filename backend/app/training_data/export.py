from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_engine
from app.services.training_data import export_training_examples, write_training_jsonl


def export_training_data(session: Session, output_path: str | Path, include_rejected: bool = False) -> int:
    examples = export_training_examples(session, include_rejected=include_rejected)
    return write_training_jsonl(examples, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export provider-neutral training data JSONL.")
    parser.add_argument("output_path", help="Path to write JSONL examples.")
    parser.add_argument("--include-rejected", action="store_true", help="Include rejected generation runs.")
    args = parser.parse_args()

    get_engine()
    with SessionLocal() as session:
        count = export_training_data(session, args.output_path, include_rejected=args.include_rejected)
    print(f"exported {count} examples to {args.output_path}")


if __name__ == "__main__":
    main()
