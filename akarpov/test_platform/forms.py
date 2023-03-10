from django import forms

from akarpov.test_platform.models import (
    BaseQuestion,
    Form,
    NumberQuestion,
    NumberRangeQuestion,
    SelectAnswerQuestion,
    SelectQuestion,
    TextQuestion,
)


class FormFormClass(forms.ModelForm):
    time_since = forms.DateField(
        widget=forms.TextInput(attrs={"type": "date"}), required=False
    )
    time_till = forms.DateField(
        widget=forms.TextInput(attrs={"type": "date"}), required=False
    )

    class Meta:
        model = Form
        fields = ["name", "description", "public", "image", "time_since", "time_till"]


class BaseQuestionForm(forms.ModelForm):
    class Meta:
        model = BaseQuestion
        fields = ["question", "help"]


class TextQuestionForm(BaseQuestionForm):
    def __init__(self, *args, **kwargs):
        super(BaseQuestionForm, self).__init__(*args, **kwargs)

    class Meta(BaseQuestionForm.Meta):
        model = TextQuestion
        fields = BaseQuestionForm.Meta.fields + [
            "correct_answer",
            "answer_should_contain",
            "answer_should_not_contain",
        ]


class NumberQuestionForm(BaseQuestionForm):
    def __init__(self, *args, **kwargs):
        super(BaseQuestionForm, self).__init__(*args, **kwargs)

    class Meta(BaseQuestionForm.Meta):
        model = NumberQuestion
        fields = BaseQuestionForm.Meta.fields + [
            "correct_answer",
        ]


class NumberRangeQuestionForm(BaseQuestionForm):
    def __init__(self, *args, **kwargs):
        super(BaseQuestionForm, self).__init__(*args, **kwargs)

    class Meta(BaseQuestionForm.Meta):
        model = NumberRangeQuestion
        fields = BaseQuestionForm.Meta.fields + [
            "number_range_min",
            "number_range_max",
        ]


class SelectQuestionForm(BaseQuestionForm):
    # {} to add index on fronted for submission
    answer = forms.CharField(
        widget=forms.TextInput(attrs={"name": "{}_answers"}), required=False
    )

    def __init__(self, *args, **kwargs):
        super(BaseQuestionForm, self).__init__(*args, **kwargs)

    class Meta(BaseQuestionForm.Meta):
        model = SelectQuestion
        fields = BaseQuestionForm.Meta.fields + [
            "min_required_answers",
            "max_required_answers",
            "answer",
        ]


class SelectAnswerQuestionForm(forms.ModelForm):
    class Meta:
        model = SelectAnswerQuestion
        fields = ["value", "correct"]
