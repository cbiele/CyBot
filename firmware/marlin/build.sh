#!/bin/zsh
# Build Marlin for the Octopus Pro V1.1 (STM32H723) with the Cybot configuration.
# Marlin lives in ./upstream (gitignored, pinned by UPSTREAM_SHA); the result lands in ./out/firmware.bin.
set -e
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
SHA=$(cat UPSTREAM_SHA)
if [ ! -d upstream ]; then
  git clone -q --filter=blob:none https://github.com/MarlinFirmware/Marlin.git upstream
fi
git -C upstream fetch -q --depth 1 origin "$SHA" 2>/dev/null || true
git -C upstream checkout -q "$SHA"
git -C upstream checkout -q -- Marlin/Configuration.h Marlin/Configuration_adv.h
python3 configure.py
pio run -d upstream -e STM32H723ZE_btt "$@"
mkdir -p out && cp upstream/.pio/build/STM32H723ZE_btt/firmware.bin out/firmware.bin
ls -la out/firmware.bin
