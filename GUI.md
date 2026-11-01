# GUI.md — ウィンドウと部品（GUI）

BASIC プログラムから、ウィンドウとボタンなどの部品（ウィジェット）を使うための仕様です。
部品のイベント（クリックなど）が起きると、そのイベントに設定した BASIC の関数（ハンドラ）が呼ばれます。
コードは `pyxel_basic_runtime/gui/` にあります。命令の一覧は [COMMANDS.md](COMMANDS.md) 4 章にもあります。

```basic
SHOW "MAIN"

FUNCTION OK_BUTTON_CLICK()
    SETPROP "MSG_LABEL", "TEXT", "こんにちは、" + GETPROP$("NAME_FIELD", "TEXT")
END FUNCTION

FUNCTION GUI_DESIGN()
    WINDOW "MAIN", "あいさつ", 20, 20, 160, 70
    WIDGET "MAIN", "TEXTFIELD", "NAME_FIELD", 6, 6, 100, 15
    WIDGET "MAIN", "BUTTON", "OK_BUTTON", 110, 6, 44, 16
    PROPERTY "OK_BUTTON", "TEXT", "OK"
    WIDGET "MAIN", "LABEL", "MSG_LABEL", 6, 30, 148, 13
    PROPERTY "MSG_LABEL", "TEXT", ""
    HANDLER "OK_BUTTON", "CLICK", "OK_BUTTON_CLICK"
END FUNCTION
```

## 1. 構成

| ファイル | 役割 |
|---|---|
| `widget.py` | 部品の基底クラス `Widget`、プロパティの定義 `PropertySpec`、共通のプロパティ |
| `widgets.py` | 標準の部品（3 章） |
| `window.py` | ウィンドウ `GuiWindow` と、`MSGBOX` のウィンドウ `MessageWindow` |
| `manager.py` | `GuiManager`: プログラムのすべてのウィンドウ・部品・ハンドラ、重なり順、入力の振り分け、イベントの待ち行列 |
| `commands.py` | BASIC の命令・関数（4 章）を `install(runtime, gui)` でコアに登録する |
| `registry.py` | 部品の種類の表（7 章） |
| `style.py` | 色・寸法・マウスカーソルなどの見た目（6 章） |

- `BasicScreen` は `GuiManager` を 1 つ持ち（`screen.gui`）、プログラムの実行ごとに作り直す。
- GUI は BASIC 画面（テキスト面・グラフィック面）の**上に重ねて**表示する。

## 2. ウィンドウ

- タイトルバー（タイトルと閉じるボックス `×`）と、部品を置くクライアント領域からなる。
- `WINDOW` で作った時点では表示されない。`SHOW` で表示し、`HIDE` で隠す。
- プロパティ: `TITLE$`（タイトル）、`X` `Y`（画面上の左上の位置）、`W` `H`（**クライアント領域**の幅と高さ）、`VISIBLE`。部品の位置はクライアント領域の左上からの座標。
- イベント: `CLOSE`（閉じるボックスが押された。ウィンドウは隠れたあとで呼ばれる）。
- 表示中のウィンドウは重なり順を持ち、いちばん手前のウィンドウ（アクティブ）がキーボードの入力を受け取る。クリックしたウィンドウが手前に来る。
- タイトルバーをドラッグすると移動できる。
- 部品のうち 1 つがフォーカスを持ち、Tab / Shift + Tab で次 / 前の部品へ移る。最初は先頭の部品がフォーカスを持つ。フォーカスのある部品は赤い枠で表示する。
- **MSGBOX** のウィンドウは画面の中央に出て、OK ボタン（または Enter / Esc）で閉じるまでいちばん手前にあり、ほかのウィンドウはクリックしても手前に来ない。

## 3. 部品

すべての部品は共通のプロパティ `X` `Y` `W` `H`（位置と大きさ）、`ENABLED`（0 なら操作できず灰色で表示）、`VISIBLE`（0 なら表示しない）を持つ。0 / 1 のプロパティにそれ以外の値を入れると `ILLEGAL FUNCTION CALL`。

| 種類 | プロパティ（初期値） | イベント | 操作 |
|---|---|---|---|
| `BUTTON` ボタン | `TEXT`（"BUTTON"） | `CLICK` | クリック（ボタンの上で離す）、Enter、スペース |
| `CHECKBOX` チェックボックス | `TEXT`（"CHECK"）、`VALUE`（0 / 1） | `CHANGE` | クリック、スペースで切り替え |
| `RADIO` ラジオボタン | `TEXT`（"RADIO"）、`VALUE`（0 / 1）、`GROUP`（"GROUP1"） | `CHANGE` | クリック、スペースでオン。同じウィンドウの同じ `GROUP` のほかのラジオボタンはオフになる（それぞれ `CHANGE`） |
| `LABEL` ラベル | `TEXT`（"LABEL"）、`COLOR`（0。0〜15） | なし | — |
| `TEXTFIELD` テキストフィールド | `TEXT`（""）、`MAXLEN`（0 = 制限なし）、`READONLY`（0 / 1） | `CHANGE`（文字が変わった）、`ENTER`（Enter が押された） | 文字の入力、Backspace / Delete、← → Home End、クリックでカーソル移動 |
| `TEXTAREA` テキストエリア | `TEXT`（""。改行は `CHR$(10)`）、`READONLY`（0 / 1） | `CHANGE` | テキストフィールドと同じ。Enter で改行、↑ ↓ で行の移動 |

- プログラムから `SETPROP` で値を変えたときは、その部品のイベントは起きない。ただし、ラジオボタンの `VALUE` を 1 にしたときにオフになった同じグループのボタンには `CHANGE` が起きる。
- `READONLY` が 1 のときも、カーソルの移動はできる。

## 4. 命令と関数

名前（ウィンドウ名・部品名）・種類・プロパティ名・イベント名は大文字と小文字を区別しない。名前はプログラム全体（すべてのウィンドウ）で重ならないようにする。

| 命令 | 説明 |
|---|---|
| `WINDOW 名前$, タイトル$, x, y, w, h` | ウィンドウを作る（表示はしない） |
| `WIDGET ウィンドウ名$, 種類$, 名前$, x, y, w, h` | ウィンドウに部品を置く |
| `PROPERTY 名前$, プロパティ$, 値` | プロパティを設定する（主に `GUI_DESIGN` の中で使う） |
| `SETPROP 名前$, プロパティ$, 値` | `PROPERTY` と同じ（プログラムの中で値を変えるとき用） |
| `HANDLER 名前$, イベント$, 関数名$` | イベントのハンドラ関数を設定する。関数は引数のない `FUNCTION` |
| `SHOW ウィンドウ名$` | ウィンドウを表示して、いちばん手前にする |
| `HIDE ウィンドウ名$` | ウィンドウを隠す（`CLOSE` イベントは起きない） |
| `MSGBOX 文字列[, タイトル$]` | メッセージのウィンドウを出し、OK が押されるまで待つ（`CHR$(10)` で改行） |

| 関数 | 説明 |
|---|---|
| `GETPROP(名前$, プロパティ$)` | 数値のプロパティの値 |
| `GETPROP$(名前$, プロパティ$)` | 文字列のプロパティの値 |

- ウィンドウの `VISIBLE` を `SETPROP` で変えると `SHOW` / `HIDE` と同じ。
- エラー: ないウィンドウ・部品・種類・プロパティ・イベント、名前の重なり、0 / 1 や 0〜15 以外の値は `ILLEGAL FUNCTION CALL`。数値と文字列の取り違え（`GETPROP` で文字列のプロパティを読むなど）は `TYPE MISMATCH`。`HANDLER` の関数がなければ `UNDEFINED FUNCTION`。
- プロパティの書き方は BASIC の命令と関数の形にした（`OK.TEXT = "X"` のような書き方は文法の変更が要るため使わない）。

## 5. プログラムの流れ

1. プログラムを読み込んだら、関数 `GUI_DESIGN()` があれば、メインプログラムより先に呼ぶ。エディタの GUI デザイナは、ウィンドウと部品の定義をこの関数としてプログラムの最後に書き込む。
2. メインプログラムを実行する（`SHOW` でウィンドウを表示するなど）。
3. メインプログラムが終わっても、表示中のウィンドウがあればイベント待ちになる。
4. 部品のイベントが起きると、ハンドラ関数の名前を待ち行列に入れる。プログラムが**手すき**のとき（メインプログラムが終わったあと、または `WAIT` 中）に、1 つずつハンドラを呼ぶ。計算中・`INPUT` 中・ハンドラの実行中に起きたイベントは、手すきになるまで待つ。`WAIT` 中に呼んだハンドラが終わると、`WAIT` の続きに戻る。
5. 終わり方:
   - `END` を実行したとき（ハンドラの中でも）は、その場で終わる（`OK - PRESS ANY KEY`）。
   - 最後のウィンドウを閉じたとき（または隠したとき）、待っているイベントもなければ終わる。キー待ちはせず、すぐに `result` が `ended` になる。
   - ウィンドウを使わなかったプログラムは、これまでどおりソースの終わりで終わる。
- ハンドラの中のエラーは、プログラムのエラーとして止まる。メインプログラムの `ON ERROR` は、ハンドラの中のエラーを捕まえない（ハンドラの中で `ON ERROR` を使えば捕まえられる）。
- ハンドラの戻り値は使わない。
- ウィンドウを表示している間は、マウスカーソルを表示する（`MOUSE` で表示していなくても、GUI 用の矢印を描く）。
- キーとマウスの入力は、まずウィンドウに渡す。ウィンドウが使わなかった入力（ウィンドウの外のクリック、ウィンドウがないときのキー）は、これまでどおり `INKEY$()` や `INPUT` に渡る。

コアの側では、イベントのために次の API を使う（[core/DESIGN.md](https://github.com/zencha201/py_basic_core/blob/main/DESIGN.md) 14）: `Runtime.call_event(name)`（引数のない関数をイベントとして呼ぶ）、`Runtime.in_event`、`Runtime.ended_by_end`、`Runtime.has_function(name)`、`MSGBOX` の待ちに使う `WaitUntil`。

## 6. 見た目

- エディタと同じ見た目にする: 白い背景・黒い文字と枠、紺のタイトルバー（手前でないウィンドウは灰色）、右下に影、フォーカスは赤い枠、選択は水色。
- 色と寸法は `style.py` にまとめてある（`COLORS`、`BAR_H` など）。
- フォントは BASIC 画面と同じ `umplus_j12r`。

## 7. Python からの部品の追加

部品の種類は `registry.py` の表で管理しており、Python から追加できる。追加した部品は BASIC の `WIDGET` で使え、エディタの GUI デザイナの部品パネルとプロパティパネルにも表示される。

```python
from pyxel_basic_runtime.gui import INT, PropertySpec, Widget, register_widget

@register_widget
class Slider(Widget):
    TYPE = "SLIDER"
    PROPERTIES = (PropertySpec("VALUE", INT, 0), PropertySpec("MAX", INT, 100))
    EVENTS = ("CHANGE",)
    DEFAULT_SIZE = (80, 15)
    FOCUSABLE = True

    def mouse_down(self, x, y):           # x, y はクライアント領域の座標
        self.set("VALUE", x * self.props["MAX"] // max(1, self.props["W"] - 1))
        self.fire("CHANGE")
        return True                       # True: ドラッグと離す操作も受け取る

    def mouse_drag(self, x, y):
        self.mouse_down(x, y)

    def draw(self, ui, x, y, focused):    # x, y は画面上の左上
        ...
```

- `PROPERTIES`: `PropertySpec(名前, INT か STR, 初期値, 選べる値)`。共通のプロパティ（3 章）は自動で付く。
- `EVENTS`: イベント名の並び。`self.fire(イベント名)` で起こす。
- 入力: `mouse_down` / `mouse_drag` / `mouse_up`（座標はクライアント領域）、`key(ev)`（フォーカスがあるとき。使ったら True）。
- `changed(名前)` はプロパティが `set` で変わったときに呼ばれる。
- 描画: `draw(ui, x, y, focused)`。`ui.font` で文字を描き、`ui.frame` でフレーム数（点滅など）を得る。
