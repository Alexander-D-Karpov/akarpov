import os
from typing import Annotated

import django
from fastapi import Cookie, Depends, FastAPI, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.requests import Request

from redirect.db.curd import LinkNotFoundException, get_link_by_slug
from redirect.db.dependency import get_db
from redirect.settings import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()
app = FastAPI()


from akarpov.tools.shortener.tasks import (  # noqa: This has to be imported strictly AFTER django setup
    save_view_meta,
)


@app.exception_handler(LinkNotFoundException)
async def unicorn_exception_handler(request: Request, exc: LinkNotFoundException):
    return HTMLResponse(
        status_code=404,
        # language=HTML
        content="""
        <html lang="en">
            <head>
                <title>Unknown Link</title>
                <style>
                    h1 {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", ui-system, sans-serif;
                        font-weight: bold;
                        font-size: medium;
                        text-align: center;
                    }
                </style>
            </head>
        <body>
            <h1>Such link doesn't exist or has been revoked</h1>
        </body>
        </html>
        """,
    )


@app.get("/{slug}")
def redirect(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    user_agent: Annotated[str | None, Header()] = None,
    sessionid: Annotated[str | None, Cookie()] = None,
) -> RedirectResponse:
    """Main route that redirects to a page based on the slug."""
    if "+" in slug:
        return RedirectResponse(url=f'/tools/shortener/p/{slug.replace("+", "")}')

    link_id, link_target = get_link_by_slug(db, slug)

    save_view_meta.apply_async(
        kwargs={
            "pk": link_id,
            "ip": request.client.host,
            "user_agent": user_agent,
            "user_id": sessionid,
        },
    )

    return RedirectResponse(
        url=(settings.relative_base + link_target)
        if link_target.startswith("/")
        else link_target
    )
