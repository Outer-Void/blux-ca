from __future__ import annotations

import json
import sys
from typing import Dict, Optional

from .core.clarity_engine import ClarityEngine


def main() -> None:
    engine = ClarityEngine()
    user_state_token: Optional[Dict] = None

    print("BLUX-cA :: Clarity Agent (stub demo)")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if text.lower() in {"exit", "quit"}:
            break

        resp = engine.process(text, user_state_token=user_state_token)
        user_state_token = resp.user_state_token

        print(f"\n[cA:{resp.intent}/{resp.emotion}] {resp.message}\n")
        # Uncomment for debugging:
        # print(json.dumps(resp.user_state_token, indent=2))
        # print(json.dumps(resp.avatar, indent=2))


if __name__ == "__main__":
    main()
