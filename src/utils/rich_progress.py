import time
from typing import Callable

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    filesize,
)
from rich.text import Text

if __name__ == "__main__":
    from rich_loguru import console
else:
    from .rich_loguru import console


class CustomRateColumn(ProgressColumn):
    """Renders human readable processing rate."""

    def __init__(self, unit: str = "it"):
        super().__init__()
        self.unit = unit

    def render(self, task: "Task") -> Text:
        """Render the speed in iterations per second."""
        speed = task.finished_speed or task.speed
        if speed is None:
            return Text("", style="progress.percentage")
        unit, prefix = filesize.pick_unit_and_suffix(
            int(speed),
            ["", "k", "M", "G", "T", "P", "E", "Z", "Y"],
            1000,
        )
        data_speed = speed / unit
        return Text(
            f"{format_number(data_speed)}{prefix}{self.unit}/s",
            style="progress.percentage",
        )


class CustomMofNCompleteColumn(ProgressColumn):
    """Renders human readable processing rate."""

    def __init__(self, separator: str = "/"):
        super().__init__()
        self.separator = separator

    def render(self, task: "Task") -> Text:
        """Show completed/total."""
        completed = int(task.completed)
        total = int(task.total) if task.total is not None else "?"
        # total_width = len(str(total))

        unit, prefix = filesize.pick_unit_and_suffix(
            int(total),
            ["", "k", "M", "G", "T", "P", "E", "Z", "Y"],
            1000,
        )

        completed = completed / unit

        if total != "?":
            total = total / unit

        return Text(
            f"{format_number(completed)}{prefix}"
            + f"{self.separator}"
            + f"{format_number(total)}{prefix}",
            style="progress.download",
        )


def format_number(number: int | float | str) -> str:
    if isinstance(number, str):
        return number
    else:
        # 整数部の桁数を取得
        int_part_length = len(str(int(number)))

        # 整数部の桁数に応じてフォーマットを変更
        if int_part_length == 1:
            # 整数部が1桁の場合、小数点以下2桁を表示
            return "{:.2f}".format(number)
        elif int_part_length == 2:
            # 整数部が2桁の場合、小数点以下1桁を表示
            return "{:.1f}".format(number)
        else:
            # 整数部が3桁以上の場合、小数点以下を表示しない
            return "{:.0f}".format(number)


class RichProgress(Progress):
    def __init__(
        self,
        unit: str = "its",
        hide_progress: bool = False,
        prefix_columns: tuple[str | ProgressColumn, ...] = (),
        suffix_columns: tuple[str | ProgressColumn, ...] = (),
        *columns: str | ProgressColumn,
        console: Console | None = console,
        auto_refresh: bool = True,
        refresh_per_second: float = 10,
        speed_estimate_period: float = 30,
        transient: bool = False,
        redirect_stdout: bool = True,
        redirect_stderr: bool = True,
        get_time: Callable[[], float] | None = None,
        disable: bool = False,
        expand: bool = False,
    ) -> None:
        super().__init__(
            *columns,
            console=console,
            auto_refresh=auto_refresh,
            refresh_per_second=refresh_per_second,
            speed_estimate_period=speed_estimate_period,
            transient=transient,
            redirect_stdout=redirect_stdout,
            redirect_stderr=redirect_stderr,
            get_time=get_time,
            disable=disable,
            expand=expand,
        )

        if not hide_progress:
            self.columns = (
                prefix_columns
                + (
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TaskProgressColumn(),
                    BarColumn(),
                    CustomMofNCompleteColumn(),
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                    CustomRateColumn(unit),
                )
                + suffix_columns
            )

        else:
            self.columns = ()


if __name__ == "__main__":
    console.print("Show progressbar")
    progress = RichProgress(unit="lines")

    with progress:
        for i in progress.track(range(30)):
            time.sleep(0.1)

    console.print("Hide progressbar")
    progress = RichProgress(unit="lines", hide_progress=True)

    with progress:
        for i in progress.track(range(30)):
            time.sleep(0.1)

    console.print("Add prefix column")

    prefix_columns = (
        SpinnerColumn(),
        SpinnerColumn(),
    )

    progress = RichProgress(unit="lines", prefix_columns=prefix_columns)

    with progress:
        for i in progress.track(range(30)):
            time.sleep(0.1)

    console.print("Add suffix column")

    suffix_columns = (SpinnerColumn(), SpinnerColumn())

    progress = RichProgress(unit="lines", suffix_columns=suffix_columns)

    with progress:
        for i in progress.track(range(30)):
            time.sleep(0.1)
