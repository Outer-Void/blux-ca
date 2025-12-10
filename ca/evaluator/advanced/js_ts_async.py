import subprocess
import tempfile
import os

class JSEvaluatorAsync:
    """
    Evaluates JS/TS code asynchronously using Node.js subprocess.
    """
    def __init__(self, name="js_async_evaluator"):
        self.name = name

    def evaluate(self, code_str):
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp_file:
                tmp_file.write(code_str)
                tmp_path = tmp_file.name

            result = subprocess.run(['node', tmp_path], capture_output=True, text=True, timeout=5)
            os.remove(tmp_path)

            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}