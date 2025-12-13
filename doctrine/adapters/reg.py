def evaluate_for_reg(text: str) -> dict:
    from doctrine.loader import RuleLoader
    from doctrine.engine import PillarsEngine

    bundle = RuleLoader().load_default_bundle()
    decision = PillarsEngine(bundle).evaluate(text)
    decision_dict = decision.__dict__.copy()
    decision_dict["signature"] = None
    return decision_dict
