from pathlib import Path

from fastmcp import FastMCP

server = FastMCP("Application Logs")

LOG_FILE = Path(__file__).parent / "payment.log"


@server.tool()
def read_payment_logs() -> str:
    """Read the payment application's logs to investigate failures."""
    return LOG_FILE.read_text()


if __name__ == "__main__":
    server.run(transport="stdio")
