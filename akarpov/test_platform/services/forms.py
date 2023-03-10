from akarpov.test_platform.forms import (
    BaseQuestionForm,
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


def _get_fields_and_class_from_type(type: str):
    for question in BaseQuestion.get_subclasses()[::-1]:
        if question.type == type:
            form = question_forms[question]
            return question, form.Meta.fields + ["required"]
    raise ValueError


def get_question_types() -> dict[BaseQuestion, BaseQuestionForm]:
    res = {}
    questions = BaseQuestion.get_subclasses()[::-1]
    for question in questions:
        res[question] = question_forms[question]
    return res


def parse_form_create(values) -> list[dict[str, str]]:
    offset: dict[str, int] = {}
    res: list[dict[str, str | bool]] = []
    question_amount = len(values.getlist("type"))
    for i in range(question_amount):
        type = values.getlist("type")[i]
        question, fields = _get_fields_and_class_from_type(type)
        res.append({"type": question})
        for field in fields:
            if field in offset:
                offset[field] += 1
            else:
                offset[field] = 0
            value = values.getlist(field)[offset[field]]
            if field == "required":
                value = True if value != "off" else False
            res[i][field] = value
    return res
