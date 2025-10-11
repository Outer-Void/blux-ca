# !/usr/bin/env python3
import json, datetime

def reflect(prompt, response):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "prompt": prompt,
        "response": response,
        "intent": "reflection"
    }
    with open("~/.config/blux-lite-gold/logs/reflections.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")