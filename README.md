# Meetily source packages for Arch Linux and CachyOS

These recipes build stable Meetily releases locally. Each package installs the
same `meetily` application and uses the same user data; install one variant per
machine. They are separate recipes so building the CPU version never requires
CUDA, ROCm, or Vulkan development packages.

| Package | Transcription backend | Intended hardware |
| --- | --- | --- |
| [`meetily`](https://aur.archlinux.org/packages/meetily) | CPU | Any supported x86-64 CPU; no GPU required |
| [`meetily-openblas`](https://aur.archlinux.org/packages/meetily-openblas) | CPU with OpenBLAS | CPU-only machines |
| [`meetily-openmp`](https://aur.archlinux.org/packages/meetily-openmp) | CPU with OpenMP | CPU-only machines |
| [`meetily-cuda`](https://aur.archlinux.org/packages/meetily-cuda) | CUDA | NVIDIA GPUs supported by the installed CUDA toolkit |
| [`meetily-vulkan`](https://aur.archlinux.org/packages/meetily-vulkan) | Vulkan | Compatible AMD, Intel, and NVIDIA GPUs |
| [`meetily-hipblas`](https://aur.archlinux.org/packages/meetily-hipblas) | ROCm/HIPBLAS | AMD GPUs supported by the installed ROCm toolchain |

Metal and CoreML are macOS backends, not Linux/AUR options. A laptop's integrated
GPU may support Vulkan; the CPU variants do not require GPU support at all.
Use a CPU variant if Vulkan is unavailable: upstream's Vulkan transcription
backend does not reliably fall back when no device/driver is present.
Backend choices above concern Whisper. They do not enable CUDA for Parakeet's
separate ONNX implementation.

CUDA, Vulkan, and HIPBLAS also enable the matching backend in the local summary
helper. The HIPBLAS recipe adds the missing feature mapping to the helper's
existing ROCm dependency and updates the pinned Whisper crate for ROCm 7's
separate data and compute types. OpenBLAS and OpenMP select Whisper's corresponding
options; the summary helper retains its default CPU/OpenMP build.

## Build locally

For this NVIDIA desktop:

```sh
cd packaging/meetily-cuda
makepkg --syncdeps --install --check
```

For a machine without a usable GPU, use `packaging/meetily` instead. `makepkg`
installs declared dependencies with your permission. AUR helpers perform that
step automatically. Build dependencies are recorded separately from runtime
dependencies; some large toolchains also supply required runtime libraries.

On memory-constrained machines, limit Rust compilation:

```sh
CARGO_BUILD_JOBS=2 CMAKE_BUILD_PARALLEL_LEVEL=2 makepkg --syncdeps --install --check
```

The summary library currently overrides CMake's job limit with its detected CPU
count; use a CPU-limited container or process affinity if that still uses too much
memory.

CUDA defaults to `all-major` architectures supported by the installed toolkit.
For a build used only on this RTX 5090, `CMAKE_CUDA_ARCHITECTURES=120` reduces
compilation work. For HIP builds without an accessible GPU (such as a clean
chroot), set `AMDGPU_TARGETS` to the intended device, for example `gfx1100`.
CI compiles CUDA for `75` and HIP for `gfx1100`, without requiring physical
GPUs. The RTX 5090 build is separately checked locally with CUDA target `120`.
Compilation does not establish runtime support on untested GPU models.
Do not redistribute a machine-specific build as a general
binary package. No GPU detection changes a package's dependencies.

## Updates and publication

All six recipes have passed CI and been pushed to AUR. Select the appropriate
package in Shelly or install with, for example, `paru -S meetily-cuda`. Normal AUR updates (`paru -Syu`, or Shelly's
update screen) rebuild that variant when its recipe changes. GPU drivers remain
managed by your distribution.

The included GitHub Actions workflows follow the Omnigent packaging pattern:
check for stable releases every six hours, propose a recipe update, build all
variants in Arch containers, merge the tested revision, and publish the verified
recipes to AUR. Failed checks block publication. Building does not receive the
AUR SSH key; a separate publication job uses `AUR_SSH_PRIVATE_KEY`.

Future CI runs use [sccache](https://github.com/mozilla/sccache) for Rust and native C/C++/CUDA/HIP compilation, with
one 1 GiB cache per variant. Clean source extraction and all package checks still
run. Compiler caches match compiler versions, inputs, and flags; changed or evicted
entries rebuild normally. The first cache-enabled run populates the caches, so
speedups begin on subsequent runs and are not guaranteed after toolchain updates.
Cache statistics appear in each build log. This only enables caching in GitHub
Actions; local AUR builds keep the standard makepkg behavior.

Publication is configured for the Snoopey maintainer account, with the publisher
key stored as a GitHub Actions secret. Actions may create and merge release
update pull requests. This workflow publishes source recipes, not
binaries, and does not install updates on users' machines.

The ONNX Runtime archive already used by upstream is downloaded and checksum
verified by makepkg before compilation; this avoids the Rust build script's
fragile download path. Meetily and its Whisper/summary engines build from source.

The Source Sans font is fetched from a pinned Adobe release with a checksum
and bundled locally, so Next.js does not fetch Google Fonts during compilation.
The font license is installed alongside the application license.

Meetily's own update checks are disabled in these builds; the Arch package
manager owns application updates. Model downloads remain managed by Meetily.

## Checks

```sh
python .github/scripts/update-release.py --self-test
python .github/scripts/update-release.py
cd packaging/meetily
makepkg --printsrcinfo | diff -u .SRCINFO -
makepkg --check
```

The package check exercises the summary helper's ping/shutdown protocol.
Successful compilation and protocol checks do not establish transcription
accuracy, microphone/system-audio capture, or GPU execution on every device.

Validation for 0.4.1 (2026-10-30): all six variants built and passed their package
checks. CPU, NVIDIA RTX 5090 (CUDA and Vulkan), AMD Radeon 610M (Vulkan), and
Intel Arc Meteor Lake (Vulkan) transcribed the same spoken sample through
Meetily's actual Whisper engine. The CUDA package on the desktop and Vulkan package on the laptop passed
installed launch and package integrity checks. Both were then uninstalled at
the user's request, ready for installation through an AUR helper. ROCm was compiled in a clean Arch container for `gfx1100`,
without a physical ROCm runtime test. Live microphone/system-audio recording
and model-generated summaries have not been tested.
