def run_batch(controller, agent, task_list):
    results = {}
    for task in task_list:
        result = controller.process_task(task, agent_name=agent.name)
        results[task] = result
    return results