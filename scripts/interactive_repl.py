def start_repl(controller, agent):
    print(f"Starting interactive REPL for {agent.name}. Type 'exit' to quit.")
    while True:
        user_input = input(">>> ")
        if user_input.lower() in ["exit", "quit"]:
            break
        output = controller.process_task(user_input, agent_name=agent.name)
        print(output)