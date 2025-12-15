# Clinical Assessment Module
# PHQ-9: Patient Health Questionnaire for Depression
# GAD-7: Generalized Anxiety Disorder Assessment

class PHQ9Assessment:
    """
    PHQ-9: Patient Health Questionnaire for Depression
    9 questions, each scored 0-3
    Total score: 0-27
    """
    
    QUESTIONS = [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling or staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself - or that you are a failure or have let yourself or your family down",
        "Trouble concentrating on things, such as reading the newspaper or watching television",
        "Moving or speaking so slowly that other people could have noticed. Or the opposite - being so fidgety or restless that you have been moving around a lot more than usual",
        "Thoughts that you would be better off dead, or of hurting yourself in some way"
    ]
    
    OPTIONS = [
        {"value": 0, "text": "Not at all"},
        {"value": 1, "text": "Several days"},
        {"value": 2, "text": "More than half the days"},
        {"value": 3, "text": "Nearly every day"}
    ]
    
    @staticmethod
    def calculate_score(answers):
        """Calculate total PHQ-9 score from answers list"""
        return sum(answers)
    
    @staticmethod
    def interpret_score(score):
        """Interpret PHQ-9 score and provide recommendations"""
        if score >= 0 and score <= 4:
            return {
                "severity": "Minimal",
                "description": "Minimal or no depression",
                "color": "#4ade80",
                "recommendation": "Your responses suggest minimal depression symptoms. Continue with self-care and healthy lifestyle practices."
            }
        elif score >= 5 and score <= 9:
            return {
                "severity": "Mild",
                "description": "Mild depression",
                "color": "#fbbf24",
                "recommendation": "Your responses suggest mild depression. Consider talking to a healthcare provider and exploring therapy or counseling options."
            }
        elif score >= 10 and score <= 14:
            return {
                "severity": "Moderate",
                "description": "Moderate depression",
                "color": "#fb923c",
                "recommendation": "Your responses suggest moderate depression. We recommend scheduling an appointment with a mental health professional for proper evaluation."
            }
        elif score >= 15 and score <= 19:
            return {
                "severity": "Moderately Severe",
                "description": "Moderately severe depression",
                "color": "#f97316",
                "recommendation": "Your responses suggest moderately severe depression. Please consult with a mental health professional soon. Treatment with therapy and/or medication may be beneficial."
            }
        else:  # 20-27
            return {
                "severity": "Severe",
                "description": "Severe depression",
                "color": "#ef4444",
                "recommendation": "Your responses suggest severe depression. Please seek professional help immediately. Contact a mental health crisis line or visit an emergency room if you're in crisis."
            }


class GAD7Assessment:
    """
    GAD-7: Generalized Anxiety Disorder Assessment
    7 questions, each scored 0-3
    Total score: 0-21
    """
    
    QUESTIONS = [
        "Feeling nervous, anxious, or on edge",
        "Not being able to stop or control worrying",
        "Worrying too much about different things",
        "Trouble relaxing",
        "Being so restless that it's hard to sit still",
        "Becoming easily annoyed or irritable",
        "Feeling afraid as if something awful might happen"
    ]
    
    OPTIONS = [
        {"value": 0, "text": "Not at all"},
        {"value": 1, "text": "Several days"},
        {"value": 2, "text": "More than half the days"},
        {"value": 3, "text": "Nearly every day"}
    ]
    
    @staticmethod
    def calculate_score(answers):
        """Calculate total GAD-7 score from answers list"""
        return sum(answers)
    
    @staticmethod
    def interpret_score(score):
        """Interpret GAD-7 score and provide recommendations"""
        if score >= 0 and score <= 4:
            return {
                "severity": "Minimal",
                "description": "Minimal anxiety",
                "color": "#4ade80",
                "recommendation": "Your responses suggest minimal anxiety. Continue practicing stress management and self-care."
            }
        elif score >= 5 and score <= 9:
            return {
                "severity": "Mild",
                "description": "Mild anxiety",
                "color": "#fbbf24",
                "recommendation": "Your responses suggest mild anxiety. Consider stress reduction techniques like mindfulness, exercise, and adequate sleep. If symptoms persist, consult a healthcare provider."
            }
        elif score >= 10 and score <= 14:
            return {
                "severity": "Moderate",
                "description": "Moderate anxiety",
                "color": "#fb923c",
                "recommendation": "Your responses suggest moderate anxiety. We recommend consulting with a mental health professional for evaluation and possible treatment options."
            }
        else:  # 15-21
            return {
                "severity": "Severe",
                "description": "Severe anxiety",
                "color": "#ef4444",
                "recommendation": "Your responses suggest severe anxiety. Please seek professional help soon. Treatment with therapy (such as CBT) and/or medication can be very effective."
            }


# Utility functions
def get_assessment_by_type(assessment_type):
    """Get assessment class by type"""
    assessments = {
        "phq9": PHQ9Assessment,
        "gad7": GAD7Assessment
    }
    return assessments.get(assessment_type.lower())


def validate_answers(answers, assessment_type):
    """Validate that answers are in correct format and range"""
    assessment_class = get_assessment_by_type(assessment_type)
    if not assessment_class:
        return False, "Invalid assessment type"
    
    expected_length = len(assessment_class.QUESTIONS)
    if len(answers) != expected_length:
        return False, f"Expected {expected_length} answers, got {len(answers)}"
    
    for i, answer in enumerate(answers):
        if not isinstance(answer, int) or answer < 0 or answer > 3:
            return False, f"Answer {i+1} must be an integer between 0 and 3"
    
    return True, "Valid"
