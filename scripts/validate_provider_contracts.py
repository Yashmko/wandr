#!/usr/bin/env python3
"""Validate Relay provider delivery/channel contracts without network calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from relay.providers import endpoint_factory


@dataclass(frozen=True)
class ProviderContract:
    channels: tuple[str, ...]
    delivery_names: tuple[str, ...]


CONTRACTS: dict[str, ProviderContract] = {
    "openai": ProviderContract(
        channels=("sandbox", "stdout", "output"),
        delivery_names=("sandbox", "stdout", "output"),
    ),
    "anthropic": ProviderContract(
        channels=("sandbox", "output"),
        delivery_names=("sandbox", "output"),
    ),
    "perplexity": ProviderContract(
        channels=("share", "output"),
        delivery_names=("share", "output"),
    ),
    "exa": ProviderContract(channels=("output",), delivery_names=("output",)),
    "parallel": ProviderContract(channels=("output",), delivery_names=("output",)),
    "gemini": ProviderContract(channels=("output",), delivery_names=("output",)),
}


def _check_provider(provider: str, contract: ProviderContract) -> None:
    factory = endpoint_factory(provider)
    seen: set[str] = set()
    for channel in contract.channels:
        endpoint = factory(model_name="dummy-model", env={}, request={}, delivery_channel=channel)
        delivery = endpoint.delivery_method
        seen.add(delivery.name)
        if delivery.name != channel:
            raise ValueError(
                f"{provider}: delivery_channel={channel!r} produced {delivery.name!r}, expected {channel!r}"
            )
    if tuple(sorted(seen)) != tuple(sorted(contract.delivery_names)):
        raise ValueError(
            f"{provider}: delivery methods mismatch: seen={sorted(seen)} expected={sorted(contract.delivery_names)}"
        )


def main() -> int:
    for provider, contract in CONTRACTS.items():
        _check_provider(provider, contract)
    print(f"provider contracts OK ({len(CONTRACTS)} providers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
