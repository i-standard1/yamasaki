#!/usr/bin/env bash
# 動作する Python インタプリタを解決し、変数 PYTHON にセットする（source して使う）。
#
# Windows では `python3` が Microsoft Store のスタブ
# （%LOCALAPPDATA%\Microsoft\WindowsApps\python3）に解決されることがある。
# スタブは標準出力に `Python` とだけ書いて exit 49 を返すため、
# `command -v python3` の存在確認だけでは使えるかどうか判定できない。
# 実際に式を評価させて確認する必要がある。
#
# 解決できた場合: PYTHON に候補（"python3" / "python" / "py -3"）をセットして return 0
# 解決できない場合: PYTHON="" のまま return 1
#
# 呼び出し側は $PYTHON をクォートせずに展開する（"py -3" を2語に分割させるため）。

resolve_python() {
  candidate=""
  for candidate in "python3" "python" "py -3"; do
    # shellcheck disable=SC2086
    if [ "$($candidate -c 'print("ok")' 2>/dev/null | tr -d '\r')" = "ok" ]; then
      PYTHON="$candidate"
      return 0
    fi
  done
  PYTHON=""
  return 1
}

PYTHON=""
resolve_python || true
