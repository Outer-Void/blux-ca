import argparse
from blux.orchestrator.controller import Controller
from blux.agent.core_agent import BLUXAgent
from blux.adaptors.dummy_local import DummyLocalAdaptor

def main():
    parser = argparse.ArgumentParser(description="BLUX-cA CLI v2")
    parser.add_argument("--task", type=str, help="Input task for the agent")
    parser.add_argument("--agent", type=str, default="BLUX-cA", help="Specify agent name")
    parser.add_argument("--batch", type=str, help="File containing batch tasks, one per line")
    parser.add_argument("--repl", action="store_true", help="Start interactive REPL")
    parser.add_argument("--query_memory", action="store_true", help="Query agent memory")

    args = parser.parse_args()

    controller = Controller()
    agent = BLUXAgent(name=args.agent)
    controller.register_agent(agent.name, agent)
    dummy_adaptor = DummyLocalAdaptor()
    controller.register_adaptor(dummy_adaptor.name, dummy_adaptor)

    # Batch execution
    if args.batch:
        with open(args.batch, 'r') as f:
            tasks = f.read().splitlines()
        for task in tasks:
            output = controller.process_task(task, agent_name=agent.name)
            print(f"[{task}] -> {output}")
        return

    # Interactive REPL
    if args.repl:
        from scripts.interactive_repl import start_repl
        start_repl(controller, agent)
        return

    # Query memory
    if args.query_memory:
        from scripts.memory_query import query_memory
        query_memory(agent)
        return

    # Single task
    if args.task:
        output = controller.process_task(args.task, agent_name=agent.name)
        print("Agent Output:", output)
    else:
        input_data = dummy_adaptor.get_input()
        output = controller.process_task(input_data, agent_name=agent.name)
        dummy_adaptor.send_output(output)

if __name__ == "__main__":
    main()