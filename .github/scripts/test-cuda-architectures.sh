#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
source packaging/meetily-cuda/PKGBUILD
fixture_dir=$(mktemp -d)
trap 'rm -rf "$fixture_dir"' EXIT
cat > "$fixture_dir/nvidia-smi" <<'MOCK'
#!/bin/sh
[ "$MOCK_GPU_OK" = yes ] || exit 4
printf '%s\n' "$MOCK_GPU_CAPABILITIES"
MOCK
cat > "$fixture_dir/nvcc" <<'MOCK'
#!/bin/sh
printf '%s\n' "$MOCK_CUDA_TARGETS"
MOCK
chmod +x "$fixture_dir/nvidia-smi" "$fixture_dir/nvcc"
export PATH="$fixture_dir:$PATH"
export MOCK_GPU_OK=yes MOCK_GPU_CAPABILITIES=$'12.0\n8.6\n12.0'
export MOCK_CUDA_TARGETS=$'compute_75\ncompute_90\ncompute_90a\ncompute_121\ncompute_120'
[[ $(_cuda_architectures) == '86;120' ]]
MOCK_GPU_OK=no
[[ $(_cuda_architectures) == '75;90;120;121' ]]
MOCK_GPU_OK=yes MOCK_GPU_CAPABILITIES='N/A'
[[ $(_cuda_architectures) == '75;90;120;121' ]]
MOCK_CUDA_TARGETS=''
if _cuda_architectures >/dev/null 2>&1; then
  echo 'Empty CUDA target discovery should fail' >&2
  exit 1
fi
printf '%s\n' 'PASS CUDA device detection, sandbox fallback, and invalid detection'
