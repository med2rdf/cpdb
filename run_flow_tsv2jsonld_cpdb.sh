#!/bin/bash

DOCKER_IMAGE="tsv2jsonld_cpdb"

output_dir="./data"

show_help() {
    docker run -it --rm \
        -v "$(pwd)/src:/src" \
        -u "$(id -u $USER):$(id -g $USER)" \
        $DOCKER_IMAGE \
        poetry run python /src/cpdb2jsonld.py exec-flow --help
}

# オプションと位置引数を処理する
positional=()
options_args=() # オプション引数用の配列
while [ $# -gt 0 ]; do
    key="$1"

    case $key in
    -h | --help)
        show_help
        exit 0
        ;;
    --output_dir)
        output_dir="$2"
        shift
        shift
        ;;
    --output_dir=*)
        ARG="$1"
        output_dir="${ARG#*=}"
        unset ARG
        shift
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

# output_dirのディレクトリが存在しない場合には作成
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi

output_dir=$(readlink -f "${output_dir}")

# DockerコンテナでPythonスクリプトを実行し、すべての引数を渡す
docker run -it --rm \
    -v "$output_dir:/output" \
    -v "$(pwd)/src:/src" \
    -u "$(id -u $USER):$(id -g $USER)" \
    $DOCKER_IMAGE \
    poetry run python /src/cpdb2jsonld.py exec-flow \
    --output-dir /output \
    "${options_args[@]}"
