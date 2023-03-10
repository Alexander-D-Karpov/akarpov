from akarpov.test_platform.models import Form


def generate_form_question(form: Form) -> str:
    res = ""
    for i, question in enumerate(form.fields.all()):
        res += question.generate_html(i)
    return res
