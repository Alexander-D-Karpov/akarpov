from typing import Annotated

import django
from fastapi import FastAPI, Depends, Header
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from starlette.requests import Request

from redirect.db.curd import get_link_by_slug, LinkNotFoundException
from redirect.db.dependency import get_db


django.setup()
app = FastAPI()


from akarpov.tools.shortener.tasks import save_view_meta # noqa: This has to be imported strictly AFTER django setup


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
def redirect(slug: str, request: Request, db: Session = Depends(get_db), user_agent: Annotated[str | None, Header()] = None) -> RedirectResponse:
    """Main route that redirects to a page based on the slug."""
    if '+' in slug:
        return RedirectResponse(url=f'/tools/shortener/p/{slug.replace("+", "")}')

    link = get_link_by_slug(db, slug)

    save_view_meta.apply_async(
        kwargs={
            "pk": link[0],
            "ip": request.client.host,
            "user_agent": user_agent,
            "user_id": 0,
        },
    )

    return RedirectResponse(url=link[1])
