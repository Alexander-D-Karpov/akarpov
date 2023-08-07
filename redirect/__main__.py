import os
import uvicorn

from redirect.settings import settings


def main():
    """Main entrypoint of the app."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    uvicorn.run(
        "redirect.app:app",
        host=settings.redirect_host,
        port=settings.redirect_port,
        reload=settings.redirect_reload
    )


if __name__ == '__main__':
    main()
