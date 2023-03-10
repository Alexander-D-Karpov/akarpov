def set_field_html_name(cls, new_name):
    """
    This creates wrapper around the normal widget rendering,
    allowing for a custom field name (new_name).
    """
    old_render = cls.widget.render

    def _widget_render_wrapper(name, value, attrs=None):
        return old_render(new_name, value, attrs)

    cls.widget.render = _widget_render_wrapper
