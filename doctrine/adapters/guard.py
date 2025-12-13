def evaluate_for_guard(text: str) -> dict:
    from doctrine.loader import RuleLoader
    from doctrine.engine import PillarsEngine

    bundle = RuleLoader().load_default_bundle()
    decision = PillarsEngine(bundle).evaluate(text)
    return decision.__dict__
