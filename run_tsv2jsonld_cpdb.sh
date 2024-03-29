#!/bin/bash

DOCKER_IMAGE="tsv2jsonld_cpdb"

show_help() {
    docker run -it --rm \
        -v "$(pwd)/src:/src" \
        -u "$(id -u $USER):$(id -g $USER)" \
        $DOCKER_IMAGE \
        poetry run python /src/cpdb2jsonld.py tsv2jsonld --help
}

# オプションと位置引数を処理する
positional=()
options_args=() # オプション引数用の配列
while [ $# -gt 0 ]; do
    case "$1" in
    -h | --help)
        show_help
        exit 0
        ;;
    --*) # "--" で始まる引数はオプションとして処理
        options_args+=("$1")
        shift
        ;;
    -*) # "-" で始まる引数はオプションとして処理
        options_args+=("$1")
        shift
        ;;
    *) # オプション以外の場合は位置引数として処理
        positional+=("$1")
        shift
        ;;
    esac
done

# 引数が足りない場合（最小限の入力ファイルと出力ファイルのパスが必要）はヘルプを表示して終了
if [ "${#positional[@]}" -lt 2 ]; then
    echo "Error: Missing arguments."
    show_help
    exit 1
fi

# 最初の2つの位置引数を入出力ファイルパスとする
input_file_path=$(readlink -f "${positional[0]}")
output_file_path="${positional[1]}"

# output_file_pathのディレクトリが存在しない場合には作成
if [ ! -d $(dirname "$output_file_path") ]; then
    mkdir -p $(dirname "$output_file_path")
fi

# output_file_pathが指すファイルが存在しない場合には空のファイルを作成
if [ ! -e "$output_file_path" ]; then
    touch "$output_file_path"
fi

output_file_path=$(readlink -f "${output_file_path}")

# DockerコンテナでPythonスクリプトを実行し、すべての引数を渡す
docker run -it --rm \
    -v "$(dirname "$input_file_path"):/input" \
    -v "$(dirname "$output_file_path"):/output" \
    -v "$(pwd)/src:/src" \
    -u "$(id -u $USER):$(id -g $USER)" \
    $DOCKER_IMAGE \
    poetry run python /src/cpdb2jsonld.py tsv2jsonld \
    /input/$(basename "$input_file_path") \
    /output/$(basename "$output_file_path") \
    "${options_args[@]}"
