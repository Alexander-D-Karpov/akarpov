from django.contrib import admin

from akarpov.test_platform.models import (
    Form,
    FormHistory,
    FormPermission,
    NumberQuestion,
    NumberRangeQuestion,
    SelectAnswerQuestion,
    SelectQuestion,
    TextQuestion,
)

admin.site.register(Form)
admin.site.register(TextQuestion)
admin.site.register(NumberQuestion)
admin.site.register(NumberRangeQuestion)
admin.site.register(SelectQuestion)
admin.site.register(SelectAnswerQuestion)
admin.site.register(FormPermission)
admin.site.register(FormHistory)
