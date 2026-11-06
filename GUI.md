# GUI.md — ウィンドウと部品（GUI）

BASIC プログラムから、ウィンドウとボタンなどの部品（ウィジェット）を使うための仕様です。
部品のイベント（クリックなど）が起きると、そのイベントに設定した BASIC の関数（ハンドラ）が呼ばれます。
コードは `retro_basic_runtime/gui/` にあります。命令の一覧は [COMMANDS.md](COMMANDS.md) 4 章にもあります。

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
| `widgets.py` | 標準の部品（3 章）のうち、ボタン・チェックボックス・ラジオボタン・ラベル・テキストフィールド・テキストエリア |
| `listbox.py` / `picture.py` / `scrollbar.py` | リストボックス / ピクチャボックス / 横・縦スクロールバー |
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
- プロパティ: `TITLE`（タイトル）、`X` `Y`（画面上の左上の位置）、`W` `H`（**クライアント領域**の幅と高さ）、`VISIBLE`、`BGCOLOR`（7。背景色。-1 にすると背景と影を描かず、うしろの BASIC 画面が見える）。部品の位置はクライアント領域の左上からの座標。
- イベント: `CLOSE`（閉じるボックスが押された。ウィンドウは隠れたあとで呼ばれる）。
- 表示中のウィンドウは重なり順を持ち、いちばん手前のウィンドウ（アクティブ）がキーボードの入力を受け取る。クリックしたウィンドウが手前に来る。
- タイトルバーをドラッグすると移動できる。
- 部品のうち 1 つがフォーカスを持ち、Tab / Shift + Tab で次 / 前の部品へ移る。最初は先頭の部品がフォーカスを持つ。フォーカスのある部品は赤い枠で表示する。
- **MSGBOX** のウィンドウは画面の中央に出て、OK ボタン（または Enter / Esc）で閉じるまでいちばん手前にあり、ほかのウィンドウはクリックしても手前に来ない。

## 3. 部品

すべての部品は共通のプロパティ `X` `Y` `W` `H`（位置と大きさ）、`ENABLED`（0 なら操作できず灰色で表示）、`VISIBLE`（0 なら表示しない）を持つ。0 / 1 のプロパティにそれ以外の値を入れると `ILLEGAL FUNCTION CALL`。

**背景色 `BGCOLOR`**: ウィンドウと標準の部品はすべて、背景色のプロパティ `BGCOLOR` を持つ。色は描画命令（`CLS` など）やラベルの `COLOR` と同じ 0〜15 の色番号で、-1 は「背景なし（透明）」（ピクチャボックスの `COLKEY` の -1 と同じ考え方）。それ以外の値は `ILLEGAL FUNCTION CALL`。`SETBGCOLOR` / `GETBGCOLOR()`（4 章）でも変更・取得できる。

| 部品 | `BGCOLOR` の初期値 | 塗る範囲 |
|---|---|---|
| ウィンドウ、ボタン | 7 | クライアント領域 / ボタンの面 |
| テキストフィールド、テキストエリア、リストボックス | 7 | 入力欄・一覧の中 |
| チェックボックス、ラジオボタン、ラベル | -1（透明。ウィンドウの背景が見える） | 部品の範囲全体 |
| ピクチャボックス | 0 | 絵のうしろ（絵が小さいときや `COLKEY` の透明色の部分に見える） |
| 横・縦スクロールバー | 1 | つまみが動く溝（矢印とつまみの色は変わらない） |

| 種類 | プロパティ（初期値） | イベント | 操作 |
|---|---|---|---|
| `BUTTON` ボタン | `TEXT`（"BUTTON"） | `CLICK` | クリック（ボタンの上で離す）、Enter、スペース |
| `CHECKBOX` チェックボックス | `TEXT`（"CHECK"）、`VALUE`（0 / 1） | `CHANGE` | クリック、スペースで切り替え |
| `RADIO` ラジオボタン | `TEXT`（"RADIO"）、`VALUE`（0 / 1）、`GROUP`（"GROUP1"） | `CHANGE` | クリック、スペースでオン。同じウィンドウの同じ `GROUP` のほかのラジオボタンはオフになる（それぞれ `CHANGE`） |
| `LABEL` ラベル | `TEXT`（"LABEL"）、`COLOR`（0。0〜15） | なし | — |
| `TEXTFIELD` テキストフィールド | `TEXT`（""）、`MAXLEN`（0 = 制限なし）、`READONLY`（0 / 1） | `CHANGE`（文字が変わった）、`ENTER`（Enter が押された） | 文字の入力、Backspace / Delete、← → Home End、クリックでカーソル移動 |
| `TEXTAREA` テキストエリア | `TEXT`（""。改行は `CHR$(10)`）、`READONLY`（0 / 1） | `CHANGE` | テキストフィールドと同じ。Enter で改行、↑ ↓ で行の移動 |
| `LISTBOX` リストボックス | `ITEMS`（""。項目を `CHR$(10)` で区切る）、`INDEX`（-1。選んだ項目の番号、0 から）、`ITEM`（選んだ項目の文字列）※、`COUNT`（項目の数）※ | `CHANGE`（選んだ項目が変わった）、`ENTER`（ダブルクリック・Enter） | クリックで選ぶ、↑ ↓ PageUp PageDown Home End、マウスホイール・右端のスクロールバーでスクロール |
| `PICTUREBOX` ピクチャボックス | `IMAGE`（0。イメージバンク 0〜2）、`U` `V`（0。バンクの中の左上）、`COLKEY`（-1。透明色、-1 はなし）、`BORDER`（1。枠の 0 / 1）、`MOUSEX` `MOUSEY`（クリックした位置）※ | `CLICK`（押した）、`DRAG`（押したまま動かした） | — |
| `HSCROLLBAR` 横スクロールバー / `VSCROLLBAR` 縦スクロールバー | `VALUE`（0）、`MIN`（0）、`MAX`（100）、`STEP`（1。矢印の 1 回の量）、`PAGE`（10。つまみの外をクリックしたときの量・つまみの大きさ） | `CHANGE`（値が変わった） | 矢印（押し続けるとくり返す）、つまみのドラッグ、つまみの外のクリック、← → / ↑ ↓、PageUp PageDown Home End、マウスホイール |

※ は読み取り専用（`GETPROP` / `GETPROP$` で読むだけ。`SETPROP` すると `ILLEGAL FUNCTION CALL`。GUI デザイナにも表示しない）。

- **リストボックス**: `ITEMS` が `""` なら項目なし。`INDEX` に -1〜項目数-1 以外を入れると `ILLEGAL FUNCTION CALL`。`ITEMS` を変えて `INDEX` の項目がなくなったときは -1 になる。項目を足すには `SETPROP "L", "ITEMS", GETPROP$("L", "ITEMS") + CHR$(10) + "新しい項目"`（空のときは `CHR$(10)` を付けない）。
- **ピクチャボックス**: イメージバンク `IMAGE` の (`U`, `V`) から、ピクチャボックスと同じ大きさの範囲を表示する。絵は `LOAD`（リソースファイル）や `IMGSET` で用意し、毎フレーム描き直すので、バンクを書き換えるとすぐに表示が変わる。`MOUSEX` `MOUSEY` はピクチャボックスの左上からの位置で、ハンドラが呼ばれるまでに次の操作があれば新しい位置になる。GUI デザイナでは絵の代わりに × 印を表示する。
- **スクロールバー**: `VALUE` は `MIN`〜`MAX` に収める（範囲外の値を入れると端の値になる。`MIN` `MAX` を変えたときも同じ）。`STEP` `PAGE` は 1 以上。

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
| `SETBGCOLOR 名前$, 色` | ウィンドウ・部品の背景色を変える（0〜15、-1 は透明。`SETPROP 名前$, "BGCOLOR", 色` と同じ） |

| 関数 | 説明 |
|---|---|
| `GETPROP(名前$, プロパティ$)` | 数値のプロパティの値 |
| `GETPROP$(名前$, プロパティ$)` | 文字列のプロパティの値 |
| `GETBGCOLOR(名前$)` | ウィンドウ・部品の背景色（0〜15、透明なら -1。`GETPROP(名前$, "BGCOLOR")` と同じ） |

- ウィンドウの `VISIBLE` を `SETPROP` で変えると `SHOW` / `HIDE` と同じ。
- Python で追加した部品は、`bgcolor_property(初期値)` を `PROPERTIES` に入れたときだけ `BGCOLOR` を持つ（7 章。ないときに `SETBGCOLOR` すると `ILLEGAL FUNCTION CALL`）。
- エラー: ないウィンドウ・部品・種類・プロパティ・イベント、名前の重なり、0 / 1 や 0〜15 などの決まった値以外、読み取り専用のプロパティへの設定は `ILLEGAL FUNCTION CALL`。数値と文字列の取り違え（`GETPROP` で文字列のプロパティを読むなど）は `TYPE MISMATCH`。`HANDLER` の関数がなければ `UNDEFINED FUNCTION`。
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
from retro_basic_runtime.gui import INT, PropertySpec, Widget, register_widget

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

- `PROPERTIES`: `PropertySpec(名前, INT か STR, 初期値, 選べる値, readonly=False)`。共通のプロパティ（3 章）は自動で付く。`readonly=True` のプロパティは部品の側で `self.props` に値を入れ、BASIC からは読むだけになる。背景色を持たせるときは `bgcolor_property(初期値)` を入れ、`draw` で `style.fill(x, y, w, h, self.props["BGCOLOR"])`（-1 なら何も塗らない）を使う。
- `check(名前, 値)` は `set` で入れる前に呼ばれ、入れる値を返す（範囲に収めるなど）。受け付けないときは `PropertyError("value", 説明)` を送出する。
- `EVENTS`: イベント名の並び。`self.fire(イベント名)` で起こす。
- 入力: `mouse_down` / `mouse_drag` / `mouse_up`（座標はクライアント領域）、`wheel(dy)`（マウスホイール。使ったら True）、`key(ev)`（フォーカスがあるとき。使ったら True）、`update(frame)`（ウィンドウの表示中、毎フレーム）。
- `changed(名前)` はプロパティが `set` で変わったときに呼ばれる。
- 描画: `draw(ui, x, y, focused)`。`ui.font` で文字を描き、`ui.frame` でフレーム数（点滅など）を得る。描く範囲を絞るときは `pyxel.clip` ではなく `ui.clip(x, y, w, h)` と `ui.unclip()` を使う（ウィンドウの外にはみ出さないように、ウィンドウの範囲と重ねて絞る）。`ui.design` は GUI デザイナで描くときに真になる。
