from akarpov.test_platform.forms import (
    NumberQuestionForm,
    NumberRangeQuestionForm,
    SelectQuestionForm,
    TextQuestionForm,
)
from akarpov.test_platform.models import (
    BaseQuestion,
    NumberQuestion,
    NumberRangeQuestion,
    SelectQuestion,
    TextQuestion,
)

question_forms = {
    TextQuestion: TextQuestionForm,
    NumberQuestion: NumberQuestionForm,
    NumberRangeQuestion: NumberRangeQuestionForm,
    SelectQuestion: SelectQuestionForm,
}


def get_question_types():
    res = {}
    questions = BaseQuestion.get_subclasses()
    for question in questions:
        res[question.type_plural] = question_forms[question]
    return res
