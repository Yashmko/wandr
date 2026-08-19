#!/usr/bin/env python3
"""Run a local Relay mock smoke test with no paid provider calls."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import PurePosixPath

from relay.core import (
    DeliveryMethod,
    EndpointResult,
    ProducedFile,
    Relay,
    RelayError,
    Workspace,
    WorkspaceSnapshot,
)


@dataclass
class _MockWorkspace(Workspace):
    writes: list[ProducedFile]

    @property
    def root(self) -> PurePosixPath:
        return PurePosixPath("/workspace")

    async def snapshot(self) -> WorkspaceSnapshot:
        return WorkspaceSnapshot(root=self.root, tree="", files=())

    async def materialize(self, files: tuple[ProducedFile, ...]) -> None:
        self.writes.extend(files)


class _FlakyEndpoint:
    def __init__(self) -> None:
        self.attempt = 0

    @property
    def delivery_method(self) -> DeliveryMethod:
        return DeliveryMethod(name="output", output_root=None)

    async def run(self, prompt: str, observer=None) -> EndpointResult:
        self.attempt += 1
        if self.attempt == 1:
            return EndpointResult(text="first attempt", files=())
        return EndpointResult(
            text="second attempt",
            files=(
                ProducedFile(
                    path=PurePosixPath("result.jsonl"),
                    content=b'{"ok": true}\n',
                    source="mock",
                ),
            ),
            usage={"input_tokens": 10, "output_tokens": 5},
            cost_usd=0.001,
            response_id=f"mock-{self.attempt}",
        )


class _EmptyFileEndpoint:
    @property
    def delivery_method(self) -> DeliveryMethod:
        return DeliveryMethod(name="output", output_root=None)

    async def run(self, prompt: str, observer=None) -> EndpointResult:
        return EndpointResult(
            text="empty",
            files=(
                ProducedFile(
                    path=PurePosixPath("result.jsonl"),
                    content=b"",
                    source="mock",
                ),
            ),
        )


async def _run() -> None:
    writes: list[ProducedFile] = []
    workspace = _MockWorkspace(writes=writes)
    relay = Relay(
        endpoint=_FlakyEndpoint(),
        workspace=workspace,
        require_files=True,
        required_file_paths=("result.jsonl",),
        max_full_restarts=1,
        full_restart_initial_delay_sec=0,
        full_restart_max_delay_sec=0,
    )
    result = await relay.run("mock")
    if len(result.files) != 1 or result.files[0].path.as_posix() != "result.jsonl":
        raise AssertionError("mock smoke expected one required file")

    try:
        await Relay(
            endpoint=_EmptyFileEndpoint(),
            workspace=_MockWorkspace(writes=[]),
            required_file_paths=("result.jsonl",),
            max_full_restarts=0,
        ).run("mock")
    except RelayError:
        return
    raise AssertionError("empty required file should fail")


def main() -> int:
    asyncio.run(_run())
    print("relay mock smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
