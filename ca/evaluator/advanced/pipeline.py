class TaskPipeline:
    """
    Chains multiple evaluators/tasks in sequence.
    Example: Python code → JS code → Bash command
    """
    def __init__(self, evaluators=None):
        if evaluators is None:
            evaluators = []
        self.evaluators = evaluators

    def add_evaluator(self, evaluator):
        self.evaluators.append(evaluator)

    def run_pipeline(self, input_data):
        """
        Executes tasks in order, passing output to next evaluator if needed.
        """
        current_input = input_data
        results = []
        for evaluator in self.evaluators:
            if hasattr(evaluator, "evaluate"):
                result = evaluator.evaluate(current_input)
            else:
                result = {"success": False, "error": "Evaluator missing evaluate()"}
            results.append(result)
            current_input = result.get("stdout") or result.get("locals") or current_input
        return results