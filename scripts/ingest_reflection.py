import os

def ingest_reflection(agent, reflections_dir):
    if not os.path.exists(reflections_dir):
        print(f"No reflections directory found: {reflections_dir}")
        return
    for filename in os.listdir(reflections_dir):
        if filename.endswith(".md"):
            with open(os.path.join(reflections_dir, filename), "r") as f:
                content = f.read()
                agent.memory.store({"input": content, "user_type": "reflection", "decision": "ingested"})
    print(f"Ingested reflections from {reflections_dir}")