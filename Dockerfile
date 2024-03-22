FROM python:3.11-slim

# poetry install用のファイル
COPY pyproject.toml /pyproject.toml
COPY poetry.lock /portry.lock

RUN apt-get update && apt-get upgrade -y

# poetryのインストール
RUN pip install -U pip && \
    pip install pipx

ENV PIPX_HOME /opt/pipx
ENV PIPX_BIN_DIR /usr/local/bin

RUN pipx install poetry

# poetryをパスに追加
ENV PATH $PATH:/usr/local/bin
ENV POETRY_VIRTUALENVS_PATH=/opt/virtualenvs

# 開発環境用のパッケージを除いてインストール
RUN poetry install --no-dev

# clean
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /usr/local/src/*

RUN rm -rf \
    ~/.cache/pip \
    ~/.cache/pipx

RUN poetry cache list \
    | xargs -i poetry cache clear {} --all
