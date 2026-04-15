/**
 * 承認ボタン用クライアントスクリプト。
 * クリック時に localhost:8765 の承認APIを叩く。mkdocs の livereload で赤背景が消える。
 */
(function () {
  var API_URL =
    (window.REVIEW_API_URL || "http://localhost:8765") + "/api/approve";

  function setup() {
    var buttons = document.querySelectorAll(".review-approve");
    buttons.forEach(function (btn) {
      if (btn.dataset.bound === "1") return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", onClick);
    });
  }

  function onClick(e) {
    e.preventDefault();
    var btn = e.currentTarget;
    var reviewId = btn.dataset.reviewId;
    var file = btn.dataset.file;

    btn.disabled = true;
    var originalText = btn.textContent;
    btn.textContent = "…";

    fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file: file, review_id: reviewId }),
    })
      .then(function (res) {
        if (!res.ok) {
          return res
            .text()
            .then(function (t) {
              throw new Error("API " + res.status + ": " + t);
            });
        }
        return res.json();
      })
      .then(function () {
        btn.textContent = "✓ 承認済";
        btn.classList.add("done");
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = originalText;
        alert(
          "承認APIに接続できません。\n" +
            "`/docs-serve` で起動してください。\n\n" +
            err.message
        );
      });
  }

  // 外部リンク（github.com 等）を新しいタブで開く
  function openExternalLinksInNewTab() {
    document.querySelectorAll("a[href]").forEach(function (a) {
      if (a.hostname && a.hostname !== location.hostname) {
        a.setAttribute("target", "_blank");
        a.setAttribute("rel", "noopener noreferrer");
      }
    });
  }

  // Material for MkDocs は instant loading を使うため、ページ遷移ごとに再バインド
  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(function () {
      setup();
      openExternalLinksInNewTab();
    });
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setup();
      openExternalLinksInNewTab();
    });
  } else {
    setup();
    openExternalLinksInNewTab();
  }
})();
