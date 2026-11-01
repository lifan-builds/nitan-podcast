"""Check the runner's saved login and target notebook before fetching content."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import shlex
import sys
from pathlib import Path

from dotenv import load_dotenv
from notebooklm import NotebookLMClient
from notebooklm.exceptions import AuthError
from notebooklm.paths import get_storage_path


async def check_access(storage: str, notebook_id: str) -> None:
    async with NotebookLMClient.from_storage(storage) as client:
        await client.notebooks.get(notebook_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args(argv)
    load_dotenv(args.env_file, override=False)
    # SDK errors can contain response bodies. Keep CI diagnostics secret-free.
    logging.disable(logging.CRITICAL)
    notebook_id = os.environ.get("NOTEBOOKLM_NOTEBOOK_ID", "").strip()
    if not notebook_id:
        print("::error::Set NOTEBOOKLM_NOTEBOOK_ID in the runner's .env.")
        return 1
    storage = os.environ.get("NOTEBOOKLM_STORAGE_PATH", "").strip() or str(get_storage_path())
    try:
        asyncio.run(asyncio.wait_for(check_access(storage, notebook_id), timeout=60))
    except (AuthError, FileNotFoundError):
        cli = Path(sys.executable).with_name("notebooklm")
        command = shlex.join([
            str(cli), "--storage", storage, "login", "--browser", "chrome", "--fresh",
        ])
        print("::error::NotebookLM login is missing or expired. On the runner Mac, "
              f"run: {command} ; then rerun this workflow. Never paste credentials into Actions.")
        return 1
    except Exception as exc:
        print(f"::error::NotebookLM preflight failed ({type(exc).__name__}). "
              "Check network access and NOTEBOOKLM_NOTEBOOK_ID; publication has not started.")
        return 1
    print("NotebookLM login and target notebook access verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
