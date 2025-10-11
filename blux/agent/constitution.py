class Constitution:
    """
    Implements core rules and spine of BLUX-cA.
    """
    def __init__(self):
        self.rules = [
            "truth_over_comfort",
            "integrity_over_approval",
            "audit_required_for_decisions"
        ]

    def apply_rules(self, user_input, user_type):
        # Simplified placeholder: returns a decision string
        if user_type == "struggler":
            return "validate and provide guidance"
        else:
            return "set boundaries / off-ramp"