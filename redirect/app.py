from typing import Annotated

import django
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.requests import Request

from redirect.db.curd import get_link_by_slug
from redirect.db.dependency import get_db


django.setup()
app = FastAPI()


from akarpov.tools.shortener.tasks import save_view_meta # noqa: This has to be imported strictly AFTER django setup


@app.get("/{slug}")
def redirect(slug: str, request: Request, db: Session = Depends(get_db), user_agent: Annotated[str | None, Header()] = None) -> RedirectResponse:
    """Main route that redirects to a page based on the slug."""
    if '+' in slug:
        return RedirectResponse(url=f'/tools/shortener/p/{slug.replace("+", "")}')

    link = get_link_by_slug(db, slug)
    if link is None:
        raise HTTPException(status_code=404, detail="Unknown Short Link")

    save_view_meta.apply_async(
        kwargs={
            "pk": link[0],
            "ip": request.client.host,
            "user_agent": user_agent,
            "user_id": 0,
        },
    )

    return RedirectResponse(url=link[1])
