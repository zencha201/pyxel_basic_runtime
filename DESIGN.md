# DESIGN.md — BASIC + Pyxel

本書は、BASIC コアを Pyxel の上で動かすパッケージ（本パッケージ）の設計書である。
使い方は [README.md](README.md)、Pyxel 版の命令・関数は [COMMANDS.md](COMMANDS.md)、言語仕様は [core/BASIC.md](https://github.com/zencha201/py_basic_core/blob/main/BASIC.md)、コアの設計は [core/DESIGN.md](https://github.com/zencha201/py_basic_core/blob/main/DESIGN.md) を参照。

- 実行基盤: Python 3.10 以降 / Pyxel 2.x（2.9.9 で動作確認）
- 使われ方: 単体の BASIC アプリとして動かす（7）ほか、エディタなどのアプリに BASIC 画面として組み込む（8）。

---

## 1. 目的と構成
- BASIC コア（`py_basic_core`）に、Pyxel による画面（文字とグラフィック）・キー入力・描画命令を組み合わせ、レトロ PC 風の BASIC 環境にする。
- **依存の規則**
  - 依存するのは `py_basic_core`（BASIC コア）と Pyxel だけ。エディタや UI 部品には依存しない。フォントの読み込みとキー入力も本パッケージの中に持つ。
  - パッケージ名は `pyxel_basic_runtime`。本パッケージの中は相対 import、コアは `py_basic_core` として import する。
  - 使う側は、リポジトリのフォルダ（`pyxel_basic_runtime` を import するため）と `core/`（`py_basic_core` を import するため）を `sys.path` に入れる。`main.py` とテストはこれを自分で行う。
  - `core/` は別のリポジトリ（[py_basic_core](https://github.com/zencha201/py_basic_core)）を git のサブモジュールとして取り込んだもの。本パッケージからは参照するだけで、変更はコアのリポジトリで行い、その後こちらで参照先を更新してコミットする。取得は `git clone --recursive`。

```
（リポジトリ）
├── pyxel_basic_runtime/        パッケージ
│   ├── __init__.py             公開 API（BasicScreen, BasicResult, Font, Input, Event, 状態の名前）
│   ├── screen.py               BasicScreen（BASIC 画面：入力・実行・描画・中断・再開）
│   ├── host.py                 PyxelHost（コアの Host の実装：文字画面のモデルへ出力）
│   ├── graphics.py             GraphicsPlane（グラフィック面）
│   ├── commands.py             CLS TEXT LINE PSET RECT RECTB CIRC CIRCB LOAD BLT IMGSET MOUSE WAIT
│   ├── functions.py            PGET BTN BTNP INKEY$ MOUSEX MOUSEY SCREENW SCREENH
│   ├── font.py                 Font（umplus_j12r.bdf の読み込み・文字幅・描画）
│   ├── input.py                Input / Event（キー・文字・クリックをフレームごとのイベントに）
│   ├── app.py                  BasicApp（単体で動かすときのアプリ）
│   └── assets/                 umplus_j12r.bdf（フォント）と利用条件
├── core/                       BASIC コア（別リポジトリ py_basic_core のサブモジュール。中の py_basic_core/ がパッケージ）
├── main.py                     起動スクリプト
├── tests/                      pytest
├── tools/build_pyxapp.py       pyxel_basic_runtime.pyxapp の作成
├── pyxel_basic_runtime.pyxapp  生成物（コードを修正したら作り直す）
├── COMMANDS.md / DESIGN.md / README.md / LICENSE
└── pytest.ini
```

---

## 2. BASIC 画面
- 画面全体を使う。背景 黒（0）・文字 白（7）。フォントは `umplus_j12r.bdf`（全角 12px・半角 6px・高さ 13px）。
- 256×240 での文字数: 横 42 桁（半角）× 縦 18 行。画面サイズから計算する。
- 行末に達したら、次の文字を書くときに次の行へ折り返す（全角文字は半角 2 桁分。行末に 1 桁しか残っていなければ全角文字は次の行へ）。最下行を超えたら 1 行ずつ上にスクロールする。
- 2 層構成（[COMMANDS.md](COMMANDS.md) 1）: グラフィック面（`pyxel.Image`）の上にテキスト面を重ねて描く。テキストの背景は透明。

**表示例**
```
READY.
PRINT 1+2
3
READY.
INPUT NAME$
? DAISUKE
READY.
PRINT NAME$
DAISUKE
READY.
```

**インライン入力（INPUT / ダイレクト実行 共通）**
- カーソル位置に入力中の文字列を表示する。ダイアログは使わない。入力が右端を超えたら折り返し、最下行を超えるときは画面をスクロールする。
- カーソルは白い箱（文字の上では色を反転）で、30 フレーム周期で点滅する。
- 使えるキー: 文字入力（IME の確定文字列を含む）、`Backspace`、`Delete`、`←` `→` `Home` `End`、`Enter`（確定）。
- ダイレクト実行では `↑` `↓` で入力履歴を呼び出す。

---

## 3. フレームとの同期（協調実行）
BASIC プログラムを別スレッドで動かさず、**Pyxel のフレームごとに少しずつ実行する**（コアの協調実行。[core/DESIGN.md](https://github.com/zencha201/py_basic_core/blob/main/DESIGN.md) 6）。
- 理由: Pyxel の描画・入力は主スレッドで扱う。Web 版（ブラウザ）ではスレッドが使えない。中断を確実に受け付けられる。
- 1 フレームの実行量: 最大 `steps_per_frame` 命令（`BasicScreen` の引数。既定 20000）、かつ最大 12ms。2000 命令ごとに経過時間を確認する。
- 実行状態ごとの画面の動作:

| 状態 | 画面の動作 |
|---|---|
| `RUNNING` | 次のフレームで続きを実行 |
| `WAITING_INPUT` | インライン入力を受け付け、確定したら `provide_input()` |
| `WAITING_FRAMES` | `WAIT n` の間、毎フレーム 1 つ数える |
| `FINISHED` / `ERROR` | プログラム実行: メッセージを出してキー待ち（4）。ダイレクト実行: `READY.` に戻る |
| `EXITED` | ダイレクト実行を終える（4） |

- グラフィック命令は即座にグラフィック面へ描き、画面への反映は毎フレームの `draw()` で行う（FLIP 不要）。

---

## 4. 終了・中断・ダイレクト実行の再開
BASIC 画面は、終わると `result`（`BasicResult(kind, message, line)`）を設定する。表示しているアプリ（単体アプリやエディタ）はそれを見て、閉じる・元の画面に戻るなどを決める。

| `kind` | いつ | 画面の動き |
|---|---|---|
| `ended` | プログラムが END / ソース終端に達した | `OK - PRESS ANY KEY` を出し、キー（またはクリック）を待ってから設定する |
| `error` | 構文エラー・実行時エラー | `?TYPE MISMATCH IN 12` と `PRESS ANY KEY` を出してキー待ち。`message` と `line`（ソースの行番号）を持つ |
| `stopped` | F5 / F6 が押された（`stop()`） | すぐに設定する |
| `exited` | ダイレクト実行で `EXIT` | すぐに設定する |

- **中断**: `update()` は**実行より先に** F5 / F6 の押下（キーリピートなし）を確認し、押されていれば `runtime.stop()` を呼んで、実行はしない。1 フレームの実行は命令数・時間で区切られるため、無限ループ中でも次のフレームで必ず中断できる。
- **閉じる**: 表示をやめる前に `close()` を呼ぶ。BASIC 側の配色（`LOAD` で変わることがある）を記録してから、開いたときの配色に戻し、マウスカーソルを非表示に戻す。
- **ダイレクト実行の再開**: 中断したダイレクト実行の画面は、捨てずに取っておけば `resume(steps_per_frame, max_call_depth, base_dir)` で続きから再開できる。

| 再開で残るもの | 変数・配列、画面の文字、グラフィック面、入力履歴、入力途中の行、BASIC 側の配色、マウスカーソルの表示状態 |
|---|---|
| 再開で変わるもの | 1 行の実行中（INPUT の入力待ちを含む）に中断していた場合、その行は打ち切り、`BREAK` と `READY.` を出して入力待ちに戻る（INPUT に入力しかけた文字列は捨てる） |
| 画面サイズが変わっていた場合 | 文字画面とグラフィック面を新しいサイズで作り直す（変数と入力履歴は残る） |

---

## 5. キー操作
| キー | 動作 |
|---|---|
| F5 / F6 | 中断する（`result` が `stopped`） |
| Enter | 入力の確定 |
| Backspace / Delete / ← → / Home / End | 入力行の編集 |
| ↑ ↓ | （ダイレクト実行）入力履歴 |
| 文字キー | 入力中は入力行へ、実行中は `INKEY$()` の入力として貯める |
| Esc | 何もしない（誤操作で中断しないため） |

---

## 6. 部品
- **BasicScreen（screen.py）**: BASIC 画面全体の制御。状態（phase）は `run`（実行中・INPUT 待ち）/ `line`（ダイレクト実行の入力待ち）/ `any_key`（終了・エラー後のキー待ち）。描画順は `cls(0)` → グラフィック面 → テキスト面の文字 → 入力中の文字列とカーソル。
- **Font（font.py）**: `umplus_j12r.bdf` を読み込み、文字幅の計測（フォントにない文字は互換文字か `?` / `〓` で代用）と描画を行う。探す順は `assets/` → Pyxel パッケージ同梱のサンプル素材。読み込みに時間がかかるので、既定のフォントは 1 つを全画面で共有する（`default_font()`）。
- **Input（input.py）**: 編集キー（キーリピート付き）・F5 / F6・文字入力・クリックを、フレームごとの `Event` の列にする。
- **GraphicsPlane（graphics.py）**: 画面と同じ大きさの `pyxel.Image`。描画命令はこの画像に描く。
- **命令・関数（commands.py / functions.py）**: [COMMANDS.md](COMMANDS.md) の命令・関数を `install(runtime, screen)` でコアに登録する。
  - 色番号は 0〜15 以外を `ILLEGAL FUNCTION CALL` とする。`BTN` / `BTNP` はキー名の文字列で指定する。
  - `LOAD` は相対パスを `base_dir` から探す。読み込むと `pyxel.images` などが置き換わり、配色が含まれていればパレットも変わる（`close()` で戻す）。
  - 描画命令・関数は `screen.graphics` をその都度参照する（画面サイズの変更でグラフィック面が作り直されても正しく描くため）。

---

## 7. 単体で動かす（app.py / main.py）
```sh
python main.py game.bas     # BAS ファイルを実行
python main.py              # ダイレクト実行
```
- コマンドラインにファイル名があればその BAS ファイルを実行し、なければダイレクト実行を始める。
- BASIC が終わったら（`result` が設定されたら）アプリを終了する。エディタがないので戻る先はない。
- 画面は 256×240、タイトルは `BASIC`。Esc ではアプリを終了しない（BASIC のプログラムが Esc キーを使えるように）。
- BAS ファイルの文字コードは UTF-8（BOM 付きを含む）、だめなら Shift_JIS 系（cp932）として読む。見つからないファイルを指定したら、エラーを表示して終了コード 1 で終わる。
- `LOAD` の基準フォルダは、実行する BAS ファイルのフォルダ。
- `main.py` は、リポジトリのフォルダと `core/` を `sys.path` に入れてから `pyxel_basic_runtime.app.main()` を呼ぶ。
- `.pyxapp`（`tools/build_pyxapp.py` で作る）には `main.py` と 2 つのパッケージ（`pyxel_basic_runtime`、`py_basic_core`）だけを入れる。テスト・ドキュメント・git のファイルは入らない。`.pyxapp` にした場合（`pyxel play` は `.pyxapp` 以外の引数を受け付けない）は、ダイレクト実行で始まる。

---

## 8. ほかのアプリへの組み込み
```python
# リポジトリのフォルダと core/ を sys.path に入れておく
from pyxel_basic_runtime import DIRECT, PROGRAM, BasicScreen

screen = BasicScreen(PROGRAM, source, steps_per_frame=20000, max_call_depth=1000,
                     base_dir=folder_of_the_program, font=None, input=None)
# 毎フレーム
screen.update()
screen.draw()
if screen.result is not None:
    screen.close()          # 配色とマウスカーソルを戻す
    ...                     # result.kind / message / line を見て元の画面へ
```
- `font` / `input` を渡すと、アプリ側のフォント（`Font` と同じ `char_width` / `width` / `displayable` / `draw` / `font` を持つもの）や入力を使える。省略すると本パッケージのものを使う。
- `pyxel.init()` はアプリ側が呼ぶ（Pyxel は 1 プロセスで 1 回しか初期化できない）。
- エディタでの使い方の例: F5 で `PROGRAM`、F6 で `DIRECT` の画面を作り、終わったらエディタに戻る。ダイレクト実行の画面は取っておき、次の F6 で `resume()` する。

---

## 9. テスト
- `tests/` を pytest で実行する（リポジトリのフォルダで `python -m pytest`）。`tests/conftest.py` がリポジトリのフォルダと `core/` を `sys.path` に入れ、headless の `BasicApp` を 1 つ作る（Pyxel の初期化は 1 回だけ）。
- `test_screen.py`: 終了・INPUT・エラー・中断・ダイレクト実行と再開・配色。`test_commands.py`: Pyxel の命令・関数。`test_app.py`: 単体で動かすときの引数・文字コード・終了。
- コアのテストはコアのリポジトリ（`core/tests/`）にある。
