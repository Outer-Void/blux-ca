import subprocess

class BashEvaluator:
    """
    Evaluates shell/Bash commands in a safe subprocess.
    """
    def __init__(self, name="bash_evaluator"):
        self.name = name

    def evaluate(self, command_str):
        try:
            result = subprocess.run(command_str, shell=True, capture_output=True, text=True, timeout=5)
            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}