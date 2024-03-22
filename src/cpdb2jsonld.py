import argparse
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Union

from pyld import jsonld
from tqdm import tqdm

import settings


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        """
        tqdmライブラリの進捗バーにログメッセージを出力するためのハンドラ

        Args:
            level (int): ログレベル
        """
        super().__init__(level)

    def emit(self, record):
        """ログレコードを処理し、tqdmの進捗バーに出力"""
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:
            self.handleError(record)


class URINotFoundException(Exception):
    """カスタム例外: URIが辞書に見つからない場合に使用"""

    def __init__(self, message="URI not found in the context."):
        self.message = message
        super().__init__(self.message)


class JsonldConversionResultTypeException(Exception):
    """JSON-LD変換結果の型が期待と異なる場合の例外"""

    def __init__(
        self,
        message="JSON-LD conversion result was an unexpected type.",
    ):
        self.message = message
        super().__init__(self.message)


# ログ設定の初期化ブロック
logger = logging.getLogger(__name__)
if settings.DEBUG:
    # DEBUGモードの場合はログレベルをDEBUGに設定
    logger.setLevel(logging.DEBUG)
else:
    # DEBUGモードでない場合はINFOレベルに設定
    logger.setLevel(logging.INFO)

# エラーログのファイルハンドラ
file_handler = logging.FileHandler(settings.ERROR_LOG_FILE_PATH)
# ログレベルをERRORに設定
file_handler.setLevel(logging.ERROR)
# ログフォーマットの設定
formatter = logging.Formatter(settings.LOG_FORMAT)
# ファイルハンドラにフォーマッタを設定し、ロガーに追加
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# TqdmLoggingHandlerのインスタンスを作成し、設定されたフォーマッタを適用後、ロガーに追加
tqdm_handler = TqdmLoggingHandler()
tqdm_handler.setFormatter(formatter)
logger.addHandler(tqdm_handler)


def main(
    input_file_path: str, output_file_path: str, hide_progress: bool
) -> None:
    """
    TSVファイルをJSON-LD形式に変換するメイン処理を実行

    Args:
        input_file_path (str): 入力TSVファイルのパス
        output_file_path (str): 出力JSONLファイルのパス
        hide_progress (bool): 進捗バーを非表示にするかどうか
    """
    # 変換処理開始のログ出力
    logger.info("Starting TSV to JSON-LD convert processing...")

    try:
        # 列名マッピングファイルの読み込み
        logger.info("Loading column mapping...")

        with open(settings.COLUMN_MAPPING_FILE_PATH, "r") as f:
            column_mapping = json.load(f)

        logger.info("Column mapping loaded.")

        # JSON-LDコンテキストファイルの読み込み
        logger.info("Loading JSON-LD context...")

        with open(settings.CONTEXT_LOCAL_FILE_PATH, "r") as f:
            context = json.load(f)["@context"]

        logger.info("JSON-LD context loaded.")

        # JSON-LDファイル内でUniProtエントリを参照するための列名を取得
        uniprot_entry_column = context[settings.UNIPROT_ENTRY_COLUMN]

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
                column_mapping.get(header, header) for header in headers
            ]

            # マルチスレッドで高速化
            with ThreadPoolExecutor() as executor:
                logger.info(
                    f"Multithread process: max_workers={executor._max_workers}"
                )
                # 各行を処理し、JSON-LD形式のデータに変換して出力ファイルへ書き込み
                for input_line in tqdm(
                    input_f,
                    total=total_lines,
                    desc="Processing",
                    unit="rows",
                    unit_scale=True,
                    leave=True,
                    disable=hide_progress,
                ):
                    json_str = executor.submit(
                        line_to_jsonld_line_str,
                        input_line,
                        mapped_headers,
                        uniprot_entry_column,
                        context,
                    )

                    output_f.write(json_str.result() + "\n")

    except Exception:
        # エラー発生時のロギング
        logger.exception(
            "An error occurred in the main function.",
        )

    finally:
        # 処理完了時のログ出力
        logger.info("TSV to JSON-LD convert processing finished.")


def line_to_jsonld_line_str(
    input_line: str,
    mapped_headers: List[str],
    uniprot_entry_column: str,
    context: Dict[str, str | Dict[str, str]],
):
    """tsvファイルの1行をJSON-LD形式のJSON Lines 1行に変換する

    Args:
        input_line (str): 変換対象のTSV 1行
        mapped_headers (List[str]): マッピングされたヘッダー
        uniprot_entry_column (str): uniprot_entryの列名
        context (Dict[str, str | Dict[str, str]]): コンテキスト情報

    Returns:
        _type_: _description_
    """
    if input_line.endswith("\n"):
        input_line = input_line.rstrip("\n")

    fields = input_line.strip().split("\t")

    parsed_fields = [parse_field(field) for field in fields]

    json_record = dict(zip(mapped_headers, parsed_fields))

    id = generate_node_id(json_record[uniprot_entry_column])

    json_record["@id"] = expand_uri(settings.NODE_ID_PREFIX, context) + id

    json_record["@type"] = expand_uri(settings.NODE_TYPE, context)

    json_record[expand_uri("bp3:name", context)] = id

    json_record[expand_uri("bp3:displayName", context)] = id

    data_sources = json_record[expand_uri("bp3:dataSource", context)]

    if isinstance(data_sources, list):
        data_sources = [
            settings.DATA_SOURCE_PREFIX + str(data_source).lower()
            for data_source in data_sources
        ]

    else:
        data_sources = settings.DATA_SOURCE_PREFIX + str(data_sources).lower()

    json_record[expand_uri("bp3:dataSource", context)] = data_sources

    evidences = json_record[expand_uri("bp3:evidence", context)]

    if isinstance(evidences, list):
        evidences = [
            settings.EVIDENCE_PREFIX + str(evidence) for evidence in evidences
        ]

    else:
        evidences = settings.EVIDENCE_PREFIX + str(evidences)

    json_record[expand_uri("bp3:evidence", context)] = evidences

    # participantの処理
    new_participants = []

    for participant in settings.PARTICIPANTS:
        if participant in settings.LITERAL_PARTICIPANTS:
            participant_data = {
                expand_uri(participant, context): json_record[
                    expand_uri(participant, context)
                ]
            }

        else:
            participant_data = {
                expand_uri(participant, context): {
                    "@id": expand_uri(participant, context)
                    + str(json_record[expand_uri(participant, context)])
                },
            }

        new_participants.append(participant_data)

        del json_record[expand_uri(participant, context)]

    json_record[expand_uri("bp3:participant", context)] = new_participants

    jsonld_record = convert_to_jsonld(json_record, context)

    jsonld_record["bp3:dataSource"] = jsonld_record.pop(
        expand_uri("bp3:dataSource", context)
    )

    jsonld_record["bp3:evidence"] = jsonld_record.pop(
        expand_uri("bp3:evidence", context)
    )

    # JSON-LD変換時に落ちてしまう情報の追加
    if "bp3:confidence" not in jsonld_record:
        jsonld_record["bp3:confidence"] = None

    jsonld_record["@context"] = settings.CONTEXT_FILE_URI

    json_str = json.dumps(jsonld_record, sort_keys=True)

    return json_str


def generate_node_id(uniprot_entries: List[str] | Any) -> str:
    """
    UniProtエントリのリストまたは単一のエントリからノードIDを生成します。

    Args:
        uniprot_entries (List[str] | Any): UniProtエントリのリスト、または単一のエントリ。

    Returns:
        str: 生成されたノードID。

    Raises:
        Exception: uniprot_entriesの処理中にエラーが発生した場合、ログに記録し、例外を再発します。
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


def parse_field(field: str) -> Union[str, int, float, List[Any], None]:
    """
    文字列フィールドを適切な型に変換

    Args:
        field (str): 変換する文字列フィールド

    Returns:
        Union[str, int, float, List[Any], None]: 変換後の値
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


def expand_uri(
    compact_uri: str, context: Dict[str, str | Dict[str, str]]
) -> str:
    """
    指定された文字列に対応するURIを拡大します。

    Parameters:
        compact_uri (str): 拡大したいURIのプレフィックス文字列
        context (Dict[str, str]): プレフィックスとURIのマッピングが含まれる辞書

    Returns:
        str: 拡大されたURI文字列

    Raises:
        URINotFoundException: 提供されたプレフィックスがcontextに見つからない場合に発生
    """
    try:
        # ':'があるかをチェック
        if ":" in compact_uri:
            # ':'を基準に文字列を2つに分割
            prefix, suffix = compact_uri.split(":", 1)
        else:
            prefix = compact_uri
            suffix = ""

        # 辞書からプレフィックスに対応するURIベースを取得
        if prefix in context:
            base_uri = context[prefix]

            if isinstance(base_uri, dict):
                base_uri = base_uri["@id"]

            # ベースURIが末尾に"#"または"/"を含まない場合、それを付加（suffixが空なら不要）
            if suffix and not (
                base_uri.endswith("#") or base_uri.endswith("/")
            ):
                base_uri += "#"
            # 完全なURIを返す（suffixが空ならベースURIのみを返す）
            return f"{base_uri}{suffix}"
        else:
            raise URINotFoundException(
                f"Prefix '{prefix}' not found in the context."
            )

    except Exception:
        logger.exception("An error occurred in the expand_uri function.")

        raise


def convert_to_jsonld(
    json_data: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    JSONデータをJSON-LD形式に変換

    Args:
        json_data (Dict[str, Any]): 変換するJSONデータ
        context (Dict[str, Any]): JSON-LDのコンテキスト

    Returns:
        Dict[str, Any]: JSON-LD形式のデータ
    """

    # JSON-LDのcompactメソッドを使用して、JSONデータを処理する
    try:
        compacted_data = jsonld.compact(
            json_data, context, options={"graph": True}
        )

    except Exception:
        # エラーが発生した場合はログに記録し、空の辞書を返す
        logger.exception(
            "An error occurred when executing jsonld.compact().",
        )

        return {}

    # compacted_dataが辞書型である場合、"@graph"キーの最初の要素を結果として返す
    try:
        if isinstance(compacted_data, dict):
            jsonld_record = compacted_data["@graph"][0]

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

    return jsonld_record


def jsonl2json(
    jsonl_file_path: str, json_file_path_prefix: str, hide_progress: bool
) -> None:
    """
    JSON LinesファイルをJSON-LD形式にまとめて変換

    Args:
        jsonl_file_path (str): 入力JSON Linesファイルのパス
        json_file_path_prefix (str): 出力JSON-LDファイルの接頭辞
        hide_progress (bool): 進捗バーを非表示にするかどうか
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

        # JSON Linesファイルを開き、データを読み込む
        with open(jsonl_file_path, "r") as jsonl_file, tqdm(
            total=total_lines,
            desc="Converting",
            unit="lines",
            unit_scale=True,
            leave=True,
            disable=hide_progress,
        ) as progressbar:
            current_size = 0

            for line in jsonl_file:
                data = json.loads(line)
                del data["@context"]
                data_list.append(data)
                current_size += len(line.encode("utf-8"))
                progressbar.update(1)

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
    data_list: List[Dict[str, Any]],
    context_data: Dict[str, Any],
    json_file_path_prefix: str,
    file_index: int,
) -> None:
    """
    一連のデータをJSON-LD形式でファイルに書き込む

    Args:
        data_list (List[Dict[str, Any]]): 書き込むデータのリスト
        context_data (Dict[str, Any]): JSON-LDのコンテキストデータ
        json_file_path_prefix (str): 出力ファイルの接頭辞
        file_index (int): ファイルインデックス番号
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


if __name__ == "__main__":
    # コマンドライン引数を解析するためのパーサーを作成
    parser = argparse.ArgumentParser(description="Convert TSV to JSONLD")

    # 入力となるTSVファイルパスの引数を追加
    parser.add_argument("tsv_file_path", help="Path to the input TSV file")

    # 出力となるJSONLファイルパスの引数を追加
    parser.add_argument(
        "output_file_path", help="Path to the output JSONL file"
    )

    # 進行状況の表示/非表示を切り替えるオプション引数を追加
    parser.add_argument(
        "--hide-progress",
        action="store_true",
        help="Show progress bar if this option is specified",
    )

    # 出力フォーマットをJSON-LD形式にするかどうかを選択するオプション引数を追加
    parser.add_argument(
        "--jsonld",
        action="store_true",
        help="If specified, output will be in JSON-LD format.",
    )

    # コマンドライン引数を解析
    args = parser.parse_args()

    # 出力フォルダのチェックと作成
    output_dir = os.path.dirname(args.output_file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 主処理関数を呼び出し
    main(args.tsv_file_path, args.output_file_path, args.hide_progress)

    # JSONLをJSON-LD形式で出力する場合の処理
    if args.jsonld:
        # 出力ファイル名から拡張子を除去して基本名を取得
        base = os.path.splitext(args.output_file_path)[0]

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
        jsonl2json(args.output_file_path, new_output_path, args.hide_progress)
