from functools import lru_cache

from config import urls as urls_conf

urls = None


def get_urls(urllist, name="") -> (list, list):
    res = []
    res_short = []
    for entry in urllist:
        if hasattr(entry, "url_patterns"):
            if entry.namespace != "admin":
                rres, rres_short = get_urls(
                    entry.url_patterns,
                    name + entry.namespace + ":" if entry.namespace else name,
                )
                res += rres
                res_short += rres_short
        else:
            res.append(
                (
                    name + entry.pattern.name if entry.pattern.name else "",
                    str(entry.pattern),
                )
            )
            res_short.append(
                (
                    entry.pattern.name,
                    str(entry.pattern),
                )
            )
    return res, res_short


@lru_cache
def urlpattern_to_js(pattern: str) -> (str, dict):
    if pattern.startswith("^"):
        return pattern
    res = ""
    kwargs = {}
    for p in pattern.split("<"):
        if ">" in p:
            rec = ""
            pn = p.split(">")
            k = pn[0].split(":")
            if len(k) == 1:
                rec = "{" + k[0] + "}"
                kwargs[k[0]] = "any"
            elif len(k) == 2:
                rec = "{" + k[1] + "}"
                kwargs[k[1]] = k[0]
            res += rec + pn[-1]
        else:
            res += p

    return res, kwargs


def get_api_path_by_url(name: str) -> tuple[str, dict] | None:
    global urls
    if not urls:
        urls, urls_short = get_urls(urls_conf.urlpatterns)
        urls = dict(urls_short) | dict(urls)

    if name in urls:
        return urlpattern_to_js(urls[name])
    return None
