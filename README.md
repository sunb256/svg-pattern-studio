# SVG Pattern Studio 0.2 — Web背景モード

既存のSVG生成機能（9種類のパターン、6レイヤー、ブレンド等）に、Webページ背景用の編集モードを追加したStreamlitアプリです。PythonのSVG生成エンジン自体は標準ライブラリのみで動作します。

## 起動（uv）

```bash
uv sync
uv run streamlit run src/svg_pattern_studio/app.py
```

localhost:8501 を開き、サイドバーの「編集モード」から **Web背景モード** または **通常のSVGモード** を選択します。

既存のuvプロジェクトに適用する場合、ZIPの `src/svg_pattern_studio` 内のファイルで同名ファイルを更新し、新規ファイルを追加してください。`pyproject.toml` に `streamlit` があれば依存パッケージの追加は不要です。

## Web背景モード

- グラデーション色と角度を設定する
- 上部・下部ごとに独立したSVGの横幅・高さを指定する
- 上部・下部それぞれに最大6枚のパターンを重ねる（位置、回転、フェード、合成モード等）
- Web表示幅を `px` または `%` で指定し、左右寄せ、端からの余白を設定する
- モバイル/タブレット/PC幅と、短い/長いページでプレビューする
- `top.svg` `bottom.svg` `example.css` `theme.json` `preview.html` をZIPで取得する

**注意:** 「下部」はスクロールできるページの一番下を意味します。画面（ビューポート）の底ではありません。プレビューもこの配置で表示します。長いページでは真ん中がグラデーションのみになります。

### 出力ZIPの内容

```text
web-background-theme.zip
├── top.svg         # 上部の透明SVG
├── bottom.svg      # 下部の透明SVG
├── example.css     # 同時配置するCSS（.page-background）
├── theme.json      # 生成パラメータ（再現用）
├── preview.html    # ローカルブラウザで開けるデモ
└── README.txt
```

Reactで利用する場合、`top.svg` と `bottom.svg` を `public/themes/` に保存して `example.css` を読み込めばOKです。

```tsx
<div className="page-background">{children}</div>
```

`example.css` は次のようなCSSを生成します。

```css
.page-background {
  min-height: 100vh;
  background-color: #14246B;
  background-image: url("/themes/top.svg"), url("/themes/bottom.svg"),
    linear-gradient(145deg, #14246B, #206CA8);
  background-position: 0% 0px, 50% calc(100% - 0px), center;
  background-size: 900px auto, 100% auto, cover;
  background-repeat: no-repeat;
}
```

背景画像はSVGなので拡大してもラスター画像のようには劣化しません。ただし**拡大による画角の変更や小画面での見え方**はプレビューで確認してください。

## 旧モード

通常のSVGモードでは、従来どおり背景色と複数パターンを1枚のSVGに描画できます。以前の `app.py` のUIを `classic_ui.py` に移しており、機能は維持しています。

## テスト

```bash
uv run --with pytest pytest -q
```

※ `theme.json` は書き出し専用です。アプリへのJSONインポート機能はありません。
