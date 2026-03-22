# Corne Notes

## Build facts

- This repo builds locally with repo-local tooling.
- Working local Python env: `.venv-zephyr`
- Working Zephyr SDK path: `.tooling/zephyr-sdk`
- `uvx west` works, but repo-local `west` in `.venv-zephyr` is more reliable.
- Before first build, run:

```bash
uv venv .venv-zephyr
uv pip install --python .venv-zephyr/bin/python -r zephyr/scripts/requirements-base.txt
.venv-zephyr/bin/west zephyr-export
.venv-zephyr/bin/west sdk install -d .tooling/zephyr-sdk
```

## Build cmds

- Left:

```bash
CCACHE_DISABLE=1 .venv-zephyr/bin/west build -p always -s zmk/app -d build/corne_left -b nice_nano -- -DZMK_CONFIG=$PWD/config -DSHIELD=corne_left -DSNIPPET=zmk-usb-logging
```

- Right:

```bash
CCACHE_DISABLE=1 .venv-zephyr/bin/west build -p always -s zmk/app -d build/corne_right -b nice_nano -- -DZMK_CONFIG=$PWD/config -DSHIELD=corne_right -DSNIPPET=zmk-usb-logging
```

## Board naming

- Do not use `nice_nano_v2` as the board arg in local west builds here.
- Correct board arg is `nice_nano`.
- In this ZMK tree, `nice_nano` defaults to revision `2.0.0`.
- Output UF2s can still be named with `nice_nano_v2` if desired.
- Local builds here resolve board files from `zmk/app/module/boards/...` first.
- That module `nice_nano_2_0_0_defconfig` is minimal and does not set
  `CONFIG_ZMK_USB`, `CONFIG_NVS`, or `CONFIG_SETTINGS_NVS`.
- Keep those enabled explicitly in repo config:
  - shared `config/corne.conf`: `CONFIG_FLASH=y`, `CONFIG_FLASH_PAGE_LAYOUT=y`,
    `CONFIG_FLASH_MAP=y`, `CONFIG_NVS=y`, `CONFIG_SETTINGS_NVS=y`
  - left only `config/boards/shields/corne/corne_left.conf`: `CONFIG_ZMK_USB=y`

## Firmware outputs

- Left UF2 build output:
  `build/corne_left/zephyr/zmk.uf2`
- Right UF2 build output:
  `build/corne_right/zephyr/zmk.uf2`
- Convenience copies:
  `firmware/corne_left-nice_nano_v2-zmk.uf2`
  `firmware/corne_right-nice_nano_v2-zmk.uf2`

## Current keymap

- Current layout is not Miryoku.
- It is a custom 42-key Corne layout based on the Canorus/do42
  `brokenaxe` QWERTY layout.
- Main source:
  `config/corne.keymap`
- Uses all 6 columns.
- `Tab` is `LGUI` on hold.
- Right outer thumb is `RALT` on tap, `RGUI` on hold.
- `Enter` is `FUNC` on hold.
- Caps Word is on both shifts combo.

## Rendered keymap

- Source render script:
  `scripts/render_keymap.sh`
- Config:
  `keymap-drawer-config.yaml`
- Main checked-in asset:
  `keymap.svg`
- PNG/PDF are intentionally ignored.

## Split battery config

- BLE must be explicitly enabled in shared config here:
  `config/corne.conf`
- Current required shared flags:

```conf
CONFIG_ZMK_BLE=y
CONFIG_ZMK_SPLIT_BLE=y
```

- Peripheral battery fetch/proxy is central-only.
- Put these only in left-half config:
  `config/boards/shields/corne/corne_left.conf`

```conf
CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=y
CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY=y
```

- Do not put those central battery flags in shared config or right-half config.
- If placed in shared config, right build warns and ignores them.

## Current battery goal

- Left/central half fetches + proxies peripheral battery level.
- This should allow apps like `zmk-battery-center` to show both halves on macOS.
- Host OS native battery UI may still show only one battery.

## Known warnings

- `config/boards` deprecation warning appears in this repo. Build still works.
- `KSCAN` deprecated warning appears. Build still works.

## Current wiring facts

- Left `C5` was remapped away from bad original pin.
- Current left columns:
  - `C0 P0.17`
  - `C1 P0.11`
  - `C2 P0.24`
  - `C3 P1.00`
  - `C4 P0.22`
  - `C5 P1.06`

## Useful checks

- Verify split BLE flags:

```bash
rg -n "CONFIG_ZMK_BLE|CONFIG_ZMK_SPLIT_BLE|CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL" build/corne_left/zephyr/.config build/corne_right/zephyr/.config
```

- Verify fresh artifacts:

```bash
ls -lh build/corne_left/zephyr/zmk.uf2 build/corne_right/zephyr/zmk.uf2
```

## Flashing

- Put each half into bootloader mode.
- Flash left with `firmware/corne_left-nice_nano_v2-zmk.uf2`
- Flash right with `firmware/corne_right-nice_nano_v2-zmk.uf2`
- As of latest known state, both halves were flashed with current layout
  incl Caps Word.
