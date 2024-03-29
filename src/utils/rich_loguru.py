from __future__ import annotations

import loguru
from loguru import logger
from rich.console import Console

console = Console(highlight=False)


def _log_formatter(record: loguru.Record) -> str:
    """Log message formatter"""
    color_map = {
        "TRACE": "dim blue",
        "DEBUG": "cyan",
        "INFO": "bold",
        "SUCCESS": "bold green",
        "WARNING": "bold yellow",
        "ERROR": "bold red",
        "CRITICAL": "bold white on red",
    }

    lvl_color = color_map.get(record["level"].name, "cyan")

    return (
        "[not bold green]{time:YYYY-MM-DD HH:mm:ss.SSS}[/not bold green] | "
        + f"[bold][{lvl_color}]{{level.name: <8}}[/{lvl_color}][/bold] | "
        + "[not bold cyan]{name}[/not bold cyan]:"
        + "[not bold cyan]{function}[/not bold cyan]:"
        + "[not bold cyan]{line}[/not bold cyan] "
        + f"- [{lvl_color}]{{message}}[/{lvl_color}]"
    )


logger.remove()
logger.add(console.print, format=_log_formatter, colorize=True, level="INFO")

if __name__ == "__main__":
    logger.trace("トレース")
    logger.debug("デバッグ")
    logger.info("情報")
    logger.success("成功")
    logger.warning("警告")
    logger.error("エラー")
    logger.critical("クリティカル")
