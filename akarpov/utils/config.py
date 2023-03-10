def build_redis_uri(
    host: str,
    port: int,
    username: str | None = None,
    password: str | None = None,
    db: str | None = None,
):
    return build_conn_uri("redis", host, port, username, password, db)


def build_conn_uri(
    proto: str,
    host: str,
    port: int,
    username: str | None = None,
    password: str | None = None,
    db: str | None = None,
):
    creds_part = ""
    if username or password:
        if username:
            creds_part = username
        if password:
            creds_part += f":{password}"
        creds_part += "@"
    uri = f"{proto}://{creds_part}{host}:{port}"
    if db:
        uri += f"/{db}"
    return uri
