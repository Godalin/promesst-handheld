#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target=${1:-aarch64}
if [[ "$target" == "native" ]]; then
    mkdir -p "$project_dir/build/native"
    cd "$project_dir/build/native"
    cmake ../.. -DCMAKE_BUILD_TYPE=Release
    cmake --build . -- -j4
    ctest --output-on-failure
elif [[ "$target" == "aarch64" ]]; then
    docker build --platform linux/arm64 -t promesst-build:aarch64 -f "$project_dir/scripts/Dockerfile" "$project_dir"
    docker run --rm --platform linux/arm64 --network none \
        -v "$project_dir:/work" promesst-build:aarch64 bash -c \
        'mkdir -p build/aarch64 && cd build/aarch64 && cmake ../.. -DCMAKE_BUILD_TYPE=Release && cmake --build . -- -j4 && ctest --output-on-failure && python3 /work/tests/smoke.py /work/build/aarch64 && python3 /work/tests/compare_original.py /work/build/aarch64'
else
    echo "Usage: bash scripts/build.sh [aarch64|native]" >&2
    exit 2
fi
