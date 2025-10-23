"""Execute a simple reflection self-test."""

from __future__ import annotations

from blux_ca.core.reflection import ReflectionEngine


def run(prompt: str = "Why integrity matters?") -> None:
    engine = ReflectionEngine()
    insight = engine.reflect(prompt)
    for idx, reason in enumerate(insight.chain, start=1):
        print(f"{idx}. {reason}")


if __name__ == "__main__":
    run()
