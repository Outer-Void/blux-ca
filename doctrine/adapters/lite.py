def evaluate_for_lite(text: str) -> dict:
    from doctrine.loader import RuleLoader
    from doctrine.engine import PillarsEngine

    bundle = RuleLoader().load_default_bundle()
    engine = PillarsEngine(bundle)
    decision = engine.evaluate(text)
    return decision.__dict__
