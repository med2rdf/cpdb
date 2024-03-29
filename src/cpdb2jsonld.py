from __future__ import annotations

import gzip
import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests
import settings
import typer
from pyld import jsonld
from typing_extensions import Annotated
from utils.custom_exception import JsonldConversionResultTypeException
from utils.rich_loguru import _log_formatter, console, logger
from utils.rich_progress import RichProgress

logger.remove()

if settings.DEBUG:
    logger.add(
        settings.DEBUG_LOG_FILE_PATH,
        backtrace=True,
        diagnose=True,
        level="DEBUG",
    )
    logger.add(
        console.print, format=_log_formatter, colorize=True, level="DEBUG"
    )
    logger.add(settings.INFO_LOG_FILE_PATH, level="DEBUG")
else:
    logger.add(
        console.print, format=_log_formatter, colorize=True, level="INFO"
    )
    logger.add(settings.INFO_LOG_FILE_PATH, level="INFO")

logger.add(settings.ERROR_LOG_FILE_PATH, level="ERROR")


# typer
app = typer.Typer()


@app.command()
def exec_flow(
    input_urls_file: Annotated[
        str,
        typer.Option(
            help="File path with the URL of the TSV file as input, "
            + "separated by a newline."
        ),
    ] = settings.URL_LIST_FILE_PATH,
    output_dir: Annotated[
        str, typer.Option(help="Path of output directory.")
    ] = settings.OUTPUT_DIR,
    hide_progress: Annotated[
        bool,
        typer.Option(help="Show progress bar if this option is specified."),
    ] = False,
    jsonld_output: Annotated[
        bool,
        typer.Option(help="If specified, output will be in JSON-LD format."),
    ] = False,
    skip_download: Annotated[
        bool, typer.Option(help="If specified, TSV downloading is skipped.")
    ] = False,
):
    """Reads a list of specified URLs, downloads TSV files,
    and converts them to JSONL or JSON-LD.

    Reads URLs from the file path of the string given as input
    and downloads TSV files from each URL.
    It then converts the downloaded TSV file to JSONL or JSON-LD format
    and saves it in the output directory.
    Display of processing progress and format selection can be optionally controlled.
    """
    logger.info("Start flow execution...")

    with open(input_urls_file) as f:
        urls = f.read().split()

    logger.info(f"Number of targets: {len(urls)} files")

    for url in urls:
        tsv_file_path = tsv_download(url, output_dir, skip_download)

        output_file_path = os.path.join(
            output_dir,
            f"{os.path.splitext(os.path.basename(tsv_file_path))[0]}.jsonl",
        )

        tsv2jsonld(
            tsv_file_path,
            output_file_path,
            hide_progress=hide_progress,
            jsonld_output=jsonld_output,
        )

    logger.info("Flow execution completed!")


def tsv_download(url: str, data_dir: str, skip_download: bool = False) -> str:
    """Download and decompress a TSV file from a specified URL.

    Downloads a TSV file from the given URL to the data directory, and if the file
    is compressed in GZIP format, it decompresses it. Returns the path to the resulting
    file after successful download and decompression.

    Args:
        url (str): The URL where the TSV file to be downloaded is located.
        data_dir (str): The path to the directory
        where the downloaded file will be stored.
        skip_download (bool): If specified, TSV downloading is skipped.

    Returns:
        str: The full path to the decompressed TSV file.

    Raises:
        Exception: An exception is raised if there
        is a failure in downloading or decompressing.

    """
    try:
        logger.info("Start downloading target files...")

        os.makedirs(data_dir, exist_ok=True)

        f_name = url.split("/")[-1]

        f_name_without_ext = os.path.splitext(f_name)[0]

        gzip_file_path = os.path.join(data_dir, f_name)

        decomp_file_path = os.path.join(data_dir, f_name_without_ext)

        if not skip_download:
            with requests.get(url, stream=True) as r:
                with open(gzip_file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)

            logger.info("Download of target file completed.")
            logger.info("Start decompression of target files...")

            with gzip.open(gzip_file_path, "rb") as gz_f:
                with open(decomp_file_path, "wb") as decomp_f:
                    shutil.copyfileobj(gz_f, decomp_f)

            logger.info("Decompression of the target file is complete.")

        else:
            logger.info("Download and decompression of target file skipped.")

        return decomp_file_path

    except Exception as e:
        logger.exception(e)

        raise


@app.command()
def tsv2jsonld(
    input_file_path: Annotated[
        str, typer.Argument(help="Path to the input TSV file.")
    ],
    output_file_path: Annotated[
        str, typer.Argument(help="Path to the output JSONL file.")
    ],
    taxonomy: Annotated[
        str,
        typer.Option(
            help="""Specify taxonomy.
            If not specified, the taxonomy is included in the file name.
            """
        ),
    ] = "",
    hide_progress: Annotated[
        bool,
        typer.Option(help="Show progress bar if this option is specified."),
    ] = False,
    jsonld_output: Annotated[
        bool,
        typer.Option(help="If specified, output will be in JSON-LD format."),
    ] = False,
) -> None:
    """
    Convert TSV format files to JSON Lines files in JSON-LD format
    """
    # 変換処理開始のログ出力
    logger.info("Starting TSV to JSON-LD convert processing...")

    try:
        # 出力フォルダのチェックと作成
        output_dir = os.path.dirname(output_file_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        taxonomy, tax_id = get_taxonomy_id(taxonomy, input_file_path)

        # 列名マッピングファイルの読み込み
        logger.info("Loading column mapping...")

        with open(
            os.path.join(settings.COLUMN_MAPPER_DIR, f"{taxonomy}.json"), "r"
        ) as f:
            column_mapper = json.load(f)

        logger.info("Column mapping loaded.")

        # JSON-LDコンテキストファイルの読み込み
        logger.info("Loading JSON-LD context...")

        with open(settings.CONTEXT_LOCAL_FILE_PATH, "r") as f:
            context = json.load(f)["@context"]

        logger.info("JSON-LD context loaded.")

        logger.info(f"Processing file: {input_file_path}")

        # 入力ファイルの総行数を計算
        with open(input_file_path, "r") as f:
            total_lines = sum(1 for line in f)

        # 入力ファイルと出力ファイルを開き、変換処理を実行
        with open(input_file_path, "r") as input_f, open(
            output_file_path, "w"
        ) as output_f:
            # ヘッダ行をスキップ
            for i in range(settings.HEADER_ROW_NUMBER - 1):
                next(input_f)
                total_lines -= 1

            # ヘッダ行の取得と加工
            headers = input_f.readline()
            total_lines -= 1

            if headers.endswith("\n"):
                headers = headers.rstrip("\n")

            headers = headers.strip(settings.HEADER_ROW_PREFIX).split("\t")

            mapped_headers = [
                column_mapper.get(header, None) for header in headers
            ]

            # マルチスレッドで高速化
            with ThreadPoolExecutor() as executor:
                logger.info(
                    f"Multithread process: max_workers={executor._max_workers}"
                )

                progress = RichProgress(
                    unit="rows", hide_progress=hide_progress
                )

                # 各行を処理し、JSON-LD形式のデータに変換して出力ファイルへ書き込み
                with progress:
                    for input_line in progress.track(
                        input_f,
                        total=total_lines,
                        description="Processing...",
                    ):
                        json_str = executor.submit(
                            line_to_jsonld_line_str,
                            input_line,
                            mapped_headers,
                            context,
                            tax_id,
                        )

                        output_f.write(json_str.result() + "\n")

        # JSONLをJSON-LD形式で出力する場合の処理
        if jsonld_output:
            # 出力ファイル名から拡張子を除去して基本名を取得
            base = os.path.splitext(output_file_path)[0]

            # 基本名を使用して新しいフォルダパスを生成
            new_folder_path = os.path.join(
                os.path.dirname(base), os.path.basename(base) + "_jsonld"
            )

            # 新しいフォルダが存在しなければ作成
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)

            # JSON-LDファイルの新しい出力パスを設定
            new_output_path = os.path.join(
                new_folder_path, os.path.basename(base) + ".jsonld"
            )

            # JSONLファイルをJSON-LD形式に変換して新しいパスに出力
            jsonl2json(output_file_path, new_output_path, hide_progress)

    except Exception:
        # エラー発生時のロギング
        logger.exception(
            "An error occurred in the main function.",
        )

        raise

    finally:
        # 処理完了時のログ出力
        logger.info("TSV to JSON-LD convert processing finished.")


def line_to_jsonld_line_str(
    input_line: str,
    mapped_headers: list[str],
    context: dict[str, str | dict[str, str]],
    tax_id: Any,
):
    """Converts a single line from a TSV file to a single line
    in JSON-LD format of JSON Lines.

    Args:
        input_line (str): The line from TSV to be converted.
        mapped_headers (list[str]): Mapped headers corresponding to the TSV columns.
        context (dict[str, str | dict[str, str]]): Context information for JSON-LD.
        tax_id (Any): Taxonomy ID associated with the record.

    Returns:
        str: The JSON-LD formatted line as a string.

    Note:
        This function parses each line from TSV, integrates mapped headers
        and their corresponding values to form a JSON-LD record,
        and outputs it as a well-formatted JSON-LD string.
    """
    if input_line.endswith("\n"):
        input_line = input_line.rstrip("\n")

    fields = input_line.strip().split("\t")

    parsed_fields: list[
        str | int | float | list[Any] | dict[str, str | list[str]] | None
    ] = [parse_field(field) for field in fields]

    json_record = dict(zip(mapped_headers, parsed_fields))

    json_record = {k: v for k, v in json_record.items() if k is not None}

    id = generate_node_id(json_record[settings.NODE_ID_COLUMN])

    json_record["@id"] = settings.NODE_ID_PREFIX + id

    json_record["@type"] = settings.NODE_TYPE

    json_record["label"] = id

    data_sources = json_record["data_source"]

    if isinstance(data_sources, list):
        data_sources = [
            settings.DATA_SOURCE_PREFIX + str(data_source).lower()
            for data_source in data_sources
        ]

    else:
        data_sources = settings.DATA_SOURCE_PREFIX + str(data_sources).lower()

    json_record["data_source"] = data_sources

    references = json_record.pop("reference")

    if isinstance(references, list):
        references = [
            settings.REFERENCE_PREFIX + str(reference)
            for reference in references
        ]

    else:
        references = settings.REFERENCE_PREFIX + str(references)

    json_record["evidence"] = {"reference": references}

    # participantの処理
    new_participants = []

    target_participants = settings.PARTICIPANTS

    if (
        settings.UNIPROT_ID_COLUMN not in json_record
        and settings.UNIPROT_ENTRY_COLUMN not in target_participants
    ):
        target_participants.append(settings.UNIPROT_ENTRY_COLUMN)

    if settings.UNIPROT_ENTRY_COLUMN not in target_participants:
        del json_record[settings.UNIPROT_ENTRY_COLUMN]

    for participant in target_participants:
        if participant in json_record:
            participant_value = json_record.get(participant)

            if isinstance(participant_value, list):
                for participant_data in participant_value:
                    participant_data = f"{participant}:{participant_data}"

                    new_participants.append(participant_data)

            else:
                participant_data = f"{participant}:{participant_value}"

                new_participants.append(participant_data)

            del json_record[participant]

    json_record["participant"] = new_participants

    json_record["taxonomy"] = f"taxid:{tax_id}"

    jsonld_record = convert_to_jsonld(json_record, context)

    json_str = json.dumps(jsonld_record, sort_keys=True)

    return json_str


def generate_node_id(uniprot_entries: list[str] | Any) -> str:
    """
    Generates a node ID from a list of UniProt entries or a single entry.

    Args:
        uniprot_entries (list[str] | Any): A list of UniProt entries, or a single entry.

    Returns:
        str: The generated node ID.

    Raises:
        Exception: If an error occurs during the processing of uniprot_entries,
        logs the issue and re-raises the exception.
    """
    try:
        if isinstance(uniprot_entries, list):
            id = "-".join(sorted(uniprot_entries))

        else:
            id = str(uniprot_entries)

    except Exception:
        logger.exception("An error occurred in the generate_node_id function.")

        raise

    return id


def parse_field(field: str) -> str | int | float | list[Any] | None:
    """
    Converts a string field into an appropriate type.

    Args:
        field (str): The string field to be converted.

    Returns:
        Union[str, int, float, list[Any], None]: The converted value.
    """
    # カンマが含まれる場合は、カンマで分割しリストとして返す
    if "," in field:
        return [parse_field(sub_field) for sub_field in field.split(",")]

    # "NA"の場合はNoneを返す
    if field == "NA":
        return None

    # 整数に変換できるか試みる。できれば整数として返す
    try:
        return int(field)

    except ValueError:
        # 整数に変換できない場合は、浮動小数点数に変換を試みる
        try:
            return float(field)

        except ValueError:
            # 浮動小数点数にも変換できない場合は、元の文字列をそのまま返す
            return field


def convert_to_jsonld(
    json_data: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    Convert JSON data to JSON-LD format.

    Args:
        json_data (dict[str, Any]): The JSON data to convert.
        context (dict[str, Any]): The JSON-LD context.

    Returns:
        dict[str, Any]: Data in JSON-LD format.
    """

    json_data = {"@context": context} | json_data

    try:
        expanded_data = jsonld.expand(json_data)

    except Exception:
        # エラーが発生した場合はログに記録し、空の辞書を返す
        logger.exception(
            f"""
            An error occurred when executing jsonld.expand().
            Target JSON:
            {json_data}
            """,
        )

        raise
    # JSON-LDのcompactメソッドを使用して、JSONデータを処理する
    try:
        compacted_data = jsonld.compact(expanded_data, context)

    except Exception:
        # エラーが発生した場合はログに記録し、空の辞書を返す
        logger.exception(
            f"""
            An error occurred when executing jsonld.compact().
            Context:
            {context}
            Target JSON:
            {expanded_data}
            """
        )

        raise

    # compacted_dataが辞書型である場合、@contextの値をcontextのURIで上書きする
    try:
        if isinstance(compacted_data, dict):
            if "@context" in compacted_data:
                compacted_data["@context"] = settings.CONTEXT_FILE_URI

        else:
            # compacted_dataが辞書型でない場合は、例外を発生させエラーログに記録する
            raise JsonldConversionResultTypeException(
                f"JSON-LD conversion result was {type(compacted_data)} type."
            )

    except JsonldConversionResultTypeException:
        logger.exception(
            "JSON-LD conversion result was an unexpected type.",
        )

        raise

    except Exception:
        logger.exception(
            "An error occurred in the convert_to_jsonld function."
        )

        raise

    return compacted_data


def jsonl2json(
    jsonl_file_path: str, json_file_path_prefix: str, hide_progress: bool
) -> None:
    """
    Bulk convert a JSON Lines file to JSON-LD format.

    Args:
        jsonl_file_path (str): Path to the input JSON Lines file.
        json_file_path_prefix (str): Prefix for the output JSON-LD file.
        hide_progress (bool): Whether to hide the progress bar or not.
    """

    # 変換処理開始のログを出力
    logger.info("Starting JSON Lines to JSON-LD convert processing...")

    try:
        # コンテキスト情報が記載されたファイルを読み込む
        with open(settings.CONTEXT_LOCAL_FILE_PATH, "r") as f:
            context_data = json.load(f)["@context"]

        file_index = 1  # 出力ファイルのインデックス初期化
        data_list = []  # 読み込んだデータを保持するリストを初期化

        with open(jsonl_file_path, "r") as f:
            total_lines = sum(1 for line in f)

        progress = RichProgress(unit="lines", hide_progress=hide_progress)

        # JSON Linesファイルを開き、データを読み込む
        with open(jsonl_file_path, "r") as jsonl_file, progress:
            current_size = 0

            for line in progress.track(
                jsonl_file,
                total=total_lines,
                description="Converting",
            ):
                data = json.loads(line)
                del data["@context"]
                data_list.append(data)
                current_size += len(line.encode("utf-8"))

                if (
                    current_size >= settings.JSONLD_MAX_FILE_SIZE
                ):  # 10MB以上になったらファイルに書き込み
                    write_jsonld_file(
                        data_list,
                        context_data,
                        json_file_path_prefix,
                        file_index,
                    )

                    data_list.clear()  # リストをリセット
                    file_index += 1  # ファイルインデックスをインクリメント
                    current_size = 0  # サイズカウントをリセット

            # 残りのデータを最後のファイルに書き込む
            if data_list:
                write_jsonld_file(
                    data_list,
                    context_data,
                    json_file_path_prefix,
                    file_index,
                )

    except Exception:
        logger.exception("An error occurred in the jsonl2json function.")

        raise

    # 変換処理終了のログを出力
    logger.info("JSON Lines to JSON-LD convert processing finished.")


def write_jsonld_file(
    data_list: list[dict[str, Any]],
    context_data: dict[str, Any],
    json_file_path_prefix: str,
    file_index: int,
) -> None:
    """
    Write a series of data to a file in JSON-LD format.

    Args:
        data_list (list[dict[str, Any]]): List of data to write.
        context_data (dict[str, Any]): Context data for JSON-LD.
        json_file_path_prefix (str): Prefix for the output file.
        file_index (int): File index number.
    """

    try:
        # 出力ファイルパスの生成
        output_path = f"{json_file_path_prefix}_{file_index:03}.jsonld"

        # 出力ファイルへの書き込み処理
        with open(output_path, "w", encoding="utf-8") as json_file:
            # JSON-LD形式のデータ構造の作成
            jsonld_data = {
                "@context": context_data,  # コンテキスト情報の設定
                "@graph": data_list,  # データ本体
            }

            # データをJSONファイルに書き込む
            json.dump(jsonld_data, json_file, ensure_ascii=False, indent=2)

            # 出力ログの生成
            logger.info(f"Written {len(data_list)} entries to {output_path}")

    except Exception:
        logger.exception(
            "An error occurred in the write_jsonld_file function."
        )

        raise


def get_taxonomy_id(tax_str: str, tsv_file_path: str) -> tuple[str, Any]:
    """
    Loads a taxonomy definition file and retrieves the tax_id
    corresponding to the provided tax_str.

    This function is used to match a taxonomy string with its taxonomy ID by looking up
    a TSV file that contains these mappings. It reads the entire TSV file into memory
    as a dictionary, then attempts to find the taxonomy ID using the provided string as
    the key. If no direct match is found and the tax_str is empty, it iterates over the
    entries in the TSV file to find a matching taxonomy name within the filename of the
    provided file path.

    Args:
        tax_str (str): The taxonomy string used as key for lookup.
        tsv_file_path (str): The file path to the input TSV file
        containing taxonomy mappings.

    Raises:
        Exception: An exception is raised if there is an issue with the taxonomy
        definition file such as incorrect format or if no matching taxonomy is found.

    Returns:
        tuple[str, Any]: A tuple containing the taxonomy_name and
        the corresponding taxonomy_id.

    Note:
        The 'settings.TAXONOMY_FILE_PATH' is expected to be defined in the module
        settings and holds the path to the taxonomy definition TSV file. Also, this
        function utilizes a logger to log info messages; it should also be defined in
        the module.
    """
    with open(settings.TAXONOMY_FILE_PATH) as f:
        tax_dict: dict[str, Any] = json.load(f)

        if isinstance(tax_dict, dict):
            if not tax_str:
                input_filename = os.path.basename(tsv_file_path)

                for tax_str, tax_id in tax_dict.items():
                    if tax_str in input_filename:
                        logger.info(f"Taxonomy: {tax_str}, ID: {tax_id}")
                        return tax_str, tax_id

                # どのtaxonomy定義ファイルのキーも合致しなかった場合
                raise Exception(
                    "The definition in the taxonomy definition file is incorrect."
                )

            else:
                tax_id = tax_dict.get(tax_str)

                if tax_id is not None:
                    logger.info(f"Taxonomy: {tax_str}, ID: {tax_id}")
                    return tax_str, tax_id

                else:
                    raise Exception(
                        "The definition in the taxonomy definition file is incorrect."
                    )

        else:
            raise Exception(
                "The definition in the taxonomy definition file is incorrect."
            )


if __name__ == "__main__":
    # Typer app
    app()
