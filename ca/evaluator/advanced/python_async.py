import asyncio
import traceback

class PythonAsyncEvaluator:
    """
    Evaluates Python code asynchronously in isolated namespaces.
    """
    def __init__(self, name="python_async_evaluator"):
        self.name = name

    async def evaluate_async(self, code_str, globals_dict=None, locals_dict=None):
        if globals_dict is None:
            globals_dict = {}
        if locals_dict is None:
            locals_dict = {}
        try:
            exec(code_str, globals_dict, locals_dict)
            await asyncio.sleep(0)  # placeholder for async context
            return {"success": True, "globals": globals_dict, "locals": locals_dict}
        except Exception as e:
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

    def evaluate(self, code_str, globals_dict=None, locals_dict=None):
        return asyncio.run(self.evaluate_async(code_str, globals_dict, locals_dict))