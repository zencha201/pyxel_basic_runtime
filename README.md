# BASIC + Pyxel

BASIC コアを Pyxel の上で動かすパッケージです。黒い背景に白い文字のレトロ PC 風の画面で、BASIC のプログラムを実行したり、1 行ずつ命令を打ち込んで実行したり（ダイレクト実行）できます。
描画（`CLS` `LINE` `CIRC` `BLT` など）、キー・ゲームパッド・マウスの入力、Pyxel のリソースファイルの読み込みにも対応しています。
ウィンドウとボタン・チェックボックス・テキストフィールド・リストボックス・スクロールバーなどの部品を使った GUI のプログラムも作れます（部品のイベントで BASIC の関数が呼ばれます）。
`HTTP` 命令で Web の API に HTTP / HTTPS のリクエストを送り、返ってきた JSON を DICT で受け取れます（[COMMANDS.md](COMMANDS.md) 5 章）。

※ 本パッケージは Pyxel を使って作った個人のプロジェクトで、Pyxel 公式のものではありません。

- Pyxel 版の命令・関数: [COMMANDS.md](COMMANDS.md)
- GUI（ウィンドウと部品）: [GUI.md](GUI.md)
- BASIC の言語仕様: [py_basic_core の BASIC.md](https://github.com/zencha201/py_basic_core/blob/main/BASIC.md)
- 設計: [DESIGN.md](DESIGN.md)

## 取得

BASIC コア（[py_basic_core](https://github.com/zencha201/py_basic_core)）を `core/` にサブモジュールとして取り込んでいるので、`--recursive` を付けて取得してください。

```sh
git clone --recursive https://github.com/zencha201/pyxel_basic_runtime.git
# すでに取得している場合
git submodule update --init
```

## 単体で動かす

```sh
pip install pyxel

python main.py game.bas     # BAS ファイルを実行（終わったらアプリも終わります）
python main.py              # ダイレクト実行（EXIT で終わります）
```

実行中に F5 または F6 を押すと、すぐに止まって終わります。

## アプリに組み込む

パッケージは `pyxel_basic_runtime/` フォルダで、BASIC コアの `py_basic_core` を使います。
アプリにこのリポジトリを（サブモジュールなどで）取り込み、リポジトリのフォルダと `core/` を `sys.path` に入れて import します。
`pyxel.init()` はアプリ側で呼んでください。

```python
import sys
sys.path[:0] = ["pyxel_basic_runtime/core", "pyxel_basic_runtime"]   # 取り込んだリポジトリのフォルダ

from pyxel_basic_runtime import PROGRAM, BasicScreen

screen = BasicScreen(PROGRAM, source, base_dir=".")
# 毎フレーム
screen.update()
screen.draw()
if screen.result is not None:      # 終わった（result.kind: ended / error / stopped / exited）
    screen.close()
```

ダイレクト実行（`DIRECT`）の画面を取っておき、あとで `resume()` すると続きから再開できます。詳しくは [DESIGN.md](DESIGN.md) 8 章を参照してください。

## フォルダ構成

| パス | 内容 |
|---|---|
| `pyxel_basic_runtime/` | パッケージ |
| `pyxel_basic_runtime/screen.py` | BASIC 画面 |
| `pyxel_basic_runtime/commands.py` / `functions.py` | Pyxel 版の命令・関数 |
| `pyxel_basic_runtime/graphics.py` / `host.py` / `font.py` / `input.py` | グラフィック面・出力先・フォント・キー入力 |
| `pyxel_basic_runtime/gui/` | GUI（ウィンドウと部品。[GUI.md](GUI.md)） |
| `pyxel_basic_runtime/app.py` | 単体で動かすときのアプリ |
| `pyxel_basic_runtime/assets/` | フォント（umplus_j12r.bdf）と利用条件 |
| `main.py` | 起動スクリプト |
| `core/` | BASIC コア（[py_basic_core](https://github.com/zencha201/py_basic_core) のサブモジュール。Pyxel に依存しない） |
| `tests/` | テスト |
| `tools/build_pyxapp.py` | `pyxel_basic_runtime.pyxapp` の作成 |

## テスト・パッケージの作成

```sh
pip install pyxel pytest
python -m pytest                    # このフォルダで実行（コアのテストは core/ で python -m pytest）
python tools/build_pyxapp.py        # pyxel_basic_runtime.pyxapp を作り直す（コードを修正したら必ず実行）
```

## ライセンス・謝辞

- 本パッケージ: MIT License（[LICENSE](LICENSE)）
- [Pyxel](https://github.com/kitao/pyxel): 画面描画・入力・フォント描画（MIT License。作者: Takashi Kitao 氏）。本パッケージには含まれません。
- `pyxel_basic_runtime/assets/umplus_j12r.bdf`: 画面のすべての文字表示に使っているビットマップフォント。Pyxel 同梱のサンプル素材を無改変で同梱しています。作者: COZ（Coji Morishita）氏、Copyright (C) 2002-2004 COZ。利用条件は [pyxel_basic_runtime/assets/FONT_LICENSE.txt](pyxel_basic_runtime/assets/FONT_LICENSE.txt)。

ゲームエンジン Pyxel を開発・公開されている Takashi Kitao 氏と貢献者の皆さま、日本語のビットマップフォントを自由な条件で公開されている COZ 氏に感謝します。
