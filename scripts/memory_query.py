def query_memory(agent, top_n=5):
    memory_summary = agent.memory.summarize_memory()
    print(f"Top {top_n} memory entries:")
    for entry in memory_summary[:top_n]:
        print(f"- {entry['input']} (weight={entry['weight']:.2f})")