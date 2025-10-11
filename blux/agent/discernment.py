class DiscernmentCompass:
    """
    Determines user type:
    - Struggler: validate and offer tools
    - Indulgent: boundary & off-ramp
    """
    def classify(self, user_input):
        # Placeholder logic: keyword based for demo
        if any(word in user_input.lower() for word in ["help", "struggle", "problem"]):
            return "struggler"
        else:
            return "indulgent"