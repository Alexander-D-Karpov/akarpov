import functools


def login_required(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.scope.get("user", False) or not self.scope["user"].is_authenticated:
            self.send_error("Auth is required")
        else:
            return func(self, *args, **kwargs)

    return wrapper
