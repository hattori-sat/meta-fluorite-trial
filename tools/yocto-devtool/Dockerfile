FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        bash binutils build-essential bzip2 ca-certificates chrpath cpio diffstat file gawk git \
        iputils-ping libegl1-mesa locales patch perl python3 \
        python3-pexpect python3-subunit rsync socat tar texinfo unzip \
        rpcsvc-proto lz4 wget xz-utils zstd \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/fluorite-devtool-entrypoint
COPY run-devtool.sh /usr/local/bin/fluorite-run-devtool
COPY run-recipe-task.sh /usr/local/bin/fluorite-run-recipe-task
RUN chmod 0755 /usr/local/bin/fluorite-devtool-entrypoint \
    /usr/local/bin/fluorite-run-devtool \
    /usr/local/bin/fluorite-run-recipe-task

ENTRYPOINT ["/usr/local/bin/fluorite-devtool-entrypoint"]
