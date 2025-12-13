from doctrine.loader import RuleLoader


def test_loads_rule_bundle_count():
    bundle = RuleLoader().load_default_bundle()
    assert len(bundle.rules) >= 150
    ids = [rule.id for rule in bundle.rules]
    assert len(ids) == len(set(ids))
