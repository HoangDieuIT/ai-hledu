from urllib.parse import urlparse
from fastapi import Header, Request


class URLFor:
    """
    Dependency class for reconstructing client-facing URLs from requests.
    """

    def __init__(
        self,
        request: Request,
        x_script_name: str | None = Header(default=None, include_in_schema=False),
        x_forwarded_proto: str | None = Header(default=None, include_in_schema=False),
    ) -> None:
        self.request = request
        self.script = x_script_name
        self.proto = x_forwarded_proto

    def __call__(self, path: str) -> str:
        scheme = self.proto or self.request.url.scheme
        netloc = self.request.url.netloc
        script = f"{self.script}/" if self.script else ""

        return f"{scheme}://{netloc}/{script}/{path}"
