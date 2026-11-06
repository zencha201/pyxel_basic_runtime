# COMMANDS.md — Pyxel 版の命令・関数

BASIC の言語仕様（文・式・標準関数）は [core/BASIC.md](https://github.com/zencha201/py_basic_core/blob/main/BASIC.md) を参照。
本書は、Pyxel 版が BASIC コアの拡張 API で追加する、画面・入力の命令と関数の仕様である。
これらは Pyxel 版にだけあり、ほかのフロントエンドには存在しないか、別の意味になりうる。

---

## 1. 画面の構成
- 画面は**テキスト面**（PRINT / INPUT の文字）と**グラフィック面**（下記命令の描画）の 2 層。テキスト面がグラフィック面の上に重なる（テキストの背景は透明）。
- 描画結果はフレーム更新（1/60 秒）ごとに自動で画面に反映する。`FLIP` 命令はない。
- 色はパレット番号 0〜15。

## 2. 命令
| 命令 | 説明 |
|---|---|
| `CLS [c]` | テキスト面を消去し、グラフィック面を色 c（省略時 0）で塗りつぶす。カーソルは左上へ |
| `TEXT x,y,s$,c` | グラフィック面の (x,y) に文字列を色 c で描く（フォントは umplus_j12r） |
| `LINE x1,y1,x2,y2,c` | 線分 |
| `PSET x,y,c` | 点 |
| `RECT x,y,w,h,c` / `RECTB x,y,w,h,c` | 塗りつぶし矩形 / 枠 |
| `CIRC x,y,r,c` / `CIRCB x,y,r,c` | 塗りつぶし円 / 円周 |
| `LOAD f$` | Pyxel のリソースファイル（`.pyxres`）を読み込む。イメージバンク・タイルマップ・サウンドが置き換わる。相対パスはプログラムのファイルがあるフォルダ（`BasicScreen` の `base_dir`）から探す。見つからなければ `FILE NOT FOUND` |
| `BLT x,y,b,u,v,w,h[,ck]` | イメージバンク b（0〜2）の (u,v) から幅 w・高さ h をグラフィック面の (x,y) に写す。w / h を負にすると左右 / 上下を反転。ck を指定するとその色を透明にする |
| `IMGSET b,x,y,s$` | イメージバンク b の (x,y) から右へ 1 行分の点を書く。s$ は 1 文字が 1 点の 16 進数（`0`〜`9`、`a`〜`f`。大文字も可）で、色番号を表す。16 進数以外の文字があれば `ILLEGAL FUNCTION CALL` |
| `MOUSE v` | v が 0 以外ならマウスカーソルを表示し、0 なら隠す（初期状態は非表示）。BASIC 画面を閉じると非表示に戻る |
| `WAIT n` | n フレーム（1 フレーム = 1/60 秒）待つ。アニメーションの速さをそろえるのに使う |

- 色番号が 0〜15 以外、イメージバンク番号が 0〜2 以外なら `ILLEGAL FUNCTION CALL`。
- 画面への反映はフレームごとに行われ、そのときまでに描いた内容が表示される。`CLS` で毎回描き直すアニメーションでは、1 画面を描き終えたところで `WAIT 1` を入れる（入れないと、描きかけの画面が表示されてちらつくことがある）。
- リソースファイルに配色（パレット）が含まれていれば、実行中はその配色になる。BASIC 画面を閉じると元の配色に戻る。
- リソースファイルは Pyxel のリソースエディタ（`pyxel edit`）で作る。
- リソースファイルを使わず、ドット絵を DATA 文で書いて `IMGSET` で画像バンクに書き込み、`BLT` で表示することもできる:
  ```basic
  FOR J=0 TO 7
      READ ROW$
      IMGSET 0,0,J,ROW$
  NEXT
  BLT 100,100,0,0,0,8,8,0      ' 色 0 を透明にして描く
  END
  DATA "00077000","0007c000","00777700","07777770"
  DATA "7c7777c7","77777777","07000070","70000007"
  ```
- 画像を使う例:
  ```basic
  LOAD "game.pyxres"
  X=100
  WHILE 1
      IF BTN("LEFT") OR BTN("GAMEPAD1_LEFT") THEN X=X-1
      IF BTN("RIGHT") OR BTN("GAMEPAD1_RIGHT") THEN X=X+1
      CLS 0
      BLT X,100,0,0,0,16,16,0
      WAIT 1
  WEND
  ```
- アニメーションの例:
  ```basic
  FOR X=0 TO 200
      CLS 0
      CIRC X,100,8,10
      WAIT 1
  NEXT
  ```

## 3. 関数
| 関数 | 説明 |
|---|---|
| `PGET(x,y)` | グラフィック面の色番号（画面外は 0） |
| `BTN(k$)` / `BTNP(k$)` | キーが押されているか / 押された瞬間か（1 / 0）。k$ はキー名（付録） |
| `INKEY$()` | 入力された文字を 1 文字ずつ取り出す（なければ `""`）。Enter は `CHR$(13)`、Backspace は `CHR$(8)` |
| `MOUSEX()` / `MOUSEY()` | マウスの座標 |
| `SCREENW()` / `SCREENH()` | 画面（グラフィック面）の幅と高さ（ドット）。画面サイズによって変わる（単体で動かすときは 256×240） |


## 4. GUI の命令と関数
ウィンドウとボタンなどの部品を使う命令と関数。詳しい仕様（部品の種類・プロパティ・イベント・プログラムの流れ）は [GUI.md](GUI.md) を参照。

| 命令 | 説明 |
|---|---|
| `WINDOW name$,title$,x,y,w,h` | ウィンドウを作る（表示はしない）。w / h はクライアント領域の大きさ |
| `WIDGET win$,type$,name$,x,y,w,h` | ウィンドウに部品を置く。type$ は `BUTTON` `CHECKBOX` `RADIO` `LABEL` `TEXTFIELD` `TEXTAREA` `LISTBOX` `PICTUREBOX` `HSCROLLBAR` `VSCROLLBAR`（と Python で追加した種類） |
| `PROPERTY name$,prop$,v` / `SETPROP name$,prop$,v` | プロパティを設定する（どちらも同じ） |
| `HANDLER name$,event$,func$` | イベント（`CLICK` `CHANGE` `ENTER` `DRAG` `CLOSE`）で呼ぶ、引数のない関数を設定する |
| `SHOW win$` / `HIDE win$` | ウィンドウを表示する（いちばん手前へ） / 隠す |
| `MSGBOX s[,title$]` | メッセージのウィンドウを出し、OK が押されるまで待つ |
| `SETBGCOLOR name$,c` | ウィンドウ・部品の背景色を変える。c は 0〜15 の色番号、-1 は透明 |

| 関数 | 説明 |
|---|---|
| `GETPROP(name$,prop$)` / `GETPROP$(name$,prop$)` | 数値 / 文字列のプロパティの値 |
| `GETBGCOLOR(name$)` | ウィンドウ・部品の背景色（透明なら -1） |

- 関数 `GUI_DESIGN()` があれば、メインプログラムより先に呼ばれる（GUI デザイナが作る部分）。
- ウィンドウを表示したプログラムは、メインプログラムが終わるとイベント待ちになり、`END` か、最後のウィンドウを閉じると終わる。

## 5. HTTP / HTTPS のリクエスト
BASIC コアの `HTTP` 命令と `HTTPSTATUS()` / `HTTPBODY$()` を、BASIC 画面では常に使えるようにしている（`install_http`）。仕様は [core/BASIC.md](https://github.com/zencha201/py_basic_core/blob/main/BASIC.md) 6.1。

```basic
DICT REQ$, RES$
REQ$("name") = "TARO"
HTTP "POST", URL$, REQ$, RES$          ' JSON で送り、返事の JSON を RES$ に平らにして受け取る
PRINT HTTPSTATUS(); " "; RES$("user.name")
```

- 返事を待つ間も画面の描画は続き、F5 / F6 で中断できる。GUI のイベントも、`WAIT` 中と同じように呼ばれる。
- フォーム形式で送るときは、ヘッダの DICT に `H$("Content-Type") = "application/x-www-form-urlencoded"` を入れて 5 番目の引数に渡す。
- つながらないときやタイムアウト（10 秒）は `NETWORK ERROR`。Web ブラウザで動かしたときは使えない（`NETWORK ERROR`）。

## 6. DICT のファイルへの保存と読み込み
BASIC コアの `DWRITE file$, d` / `DREAD file$, d` を、BASIC 画面では常に使えるようにしている（`install_dict_files`）。仕様は [core/BASIC.md](https://github.com/zencha201/py_basic_core/blob/main/BASIC.md) 6.2。

```basic
DICT SAVE$
SAVE$("name") = "TARO"
DWRITE "save.json", SAVE$        ' JSON で書き出す
DREAD "save.json", SAVE$         ' 読み戻す
```

- 相対パスは `LOAD` と同じく、プログラムのファイルがあるフォルダ（`BasicScreen` の `base_dir`）から探す。エディタでまだ保存していない文書を実行したときは、アプリを起動したフォルダになる。

## 付録. BTN / BTNP のキー名
大文字小文字は区別しない。

**キーボード・マウス**
```
A〜Z  0〜9  LEFT RIGHT UP DOWN  SPACE ENTER ESC TAB BACKSPACE  SHIFT CTRL ALT
MOUSE_LEFT MOUSE_RIGHT
```

**ゲームパッド**（n は 1〜4。何台目のパッドか）
```
GAMEPADn_A  GAMEPADn_B  GAMEPADn_X  GAMEPADn_Y
GAMEPADn_UP  GAMEPADn_DOWN  GAMEPADn_LEFT  GAMEPADn_RIGHT        方向ボタン
GAMEPADn_START  GAMEPADn_BACK  GAMEPADn_GUIDE
GAMEPADn_LEFTSHOULDER  GAMEPADn_RIGHTSHOULDER  GAMEPADn_LEFTSTICK  GAMEPADn_RIGHTSTICK
```
例: `IF BTN("LEFT") OR BTN("GAMEPAD1_LEFT") THEN X=X-1`、`IF BTNP("GAMEPAD1_A") THEN GOSUB JUMP`

- アナログスティックの傾き・トリガーの量は取得できない（今後の予定）。
