"""MCP entrypoint. Selects transport via MCP_TRANSPORT env var."""

from app.core.config import settings
from app.core.logging import configure_logging, get_logger


def main() -> None:
    configure_logging()
    logger = get_logger("mcp.main")
    logger.info("mcp_starting", transport=settings.MCP_TRANSPORT)

    if settings.MCP_TRANSPORT == "stdio":
        from app.transport import stdio

        stdio.run()
    elif settings.MCP_TRANSPORT == "sse":
        from app.transport import sse

        sse.run()
    else:  # pragma: no cover - Literal type narrows this away
        raise SystemExit(f"Unknown MCP_TRANSPORT: {settings.MCP_TRANSPORT}")


if __name__ == "__main__":
    main()
