/* Tinkerlab cookie consent. Shared by every page (served from /consent.js).
   Choice is stored in this browser only. Nothing non-essential (e.g. ads) should load
   unless window.tinkerlabConsent() returns "granted". */
(function () {
  var KEY = "tinkerlab_consent";
  function read() { try { var v = JSON.parse(localStorage.getItem(KEY) || "null"); return v && v.choice ? v.choice : null; } catch (e) { return null; } }
  function write(choice) {
    try { localStorage.setItem(KEY, JSON.stringify({ choice: choice, date: new Date().toISOString() })); } catch (e) {}
    try { window.dispatchEvent(new CustomEvent("tinkerlab-consent", { detail: choice })); } catch (e) {}
  }
  window.tinkerlabConsent = read;

  function css() {
    if (document.getElementById("tl-consent-css")) return;
    var s = document.createElement("style"); s.id = "tl-consent-css";
    s.textContent =
      "#tl-consent{position:fixed;left:12px;right:12px;bottom:12px;max-width:560px;margin:0 auto;background:#fff;color:#222;border-radius:14px;box-shadow:0 6px 28px rgba(0,0,0,.22);padding:16px 18px;z-index:99999;font:14px/1.45 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}" +
      "#tl-consent h2{margin:0 0 6px;font-size:1rem}" +
      "#tl-consent p{margin:0 0 12px;color:#444}" +
      "#tl-consent a{color:#2a6fdb}" +
      "#tl-consent .tl-row{display:flex;gap:10px;flex-wrap:wrap}" +
      "#tl-consent button{flex:1 1 140px;padding:10px 14px;border-radius:9px;border:2px solid #222;background:#fff;color:#222;font:600 14px inherit;cursor:pointer}" +
      "#tl-consent button:hover{background:#f0f0f0}" +
      "#tl-consent button:focus-visible{outline:3px solid #2a6fdb;outline-offset:2px}";
    document.head.appendChild(s);
  }
  function close() { var b = document.getElementById("tl-consent"); if (b) b.remove(); }
  function open() {
    if (document.getElementById("tl-consent")) return;
    css();
    var b = document.createElement("div");
    b.id = "tl-consent"; b.setAttribute("role", "dialog"); b.setAttribute("aria-label", "Cookie preferences");
    b.innerHTML =
      "<h2>Cookies &amp; your privacy</h2>" +
      "<p>Tinkerlab saves your scores in your own browser and uses privacy-friendly analytics. If we show ads in future, they may use cookies, and only if you accept. You can change your mind any time. See our <a href=\"/privacy/\">privacy policy</a>.</p>" +
      "<div class=\"tl-row\"><button type=\"button\" id=\"tl-reject\">Reject non-essential</button><button type=\"button\" id=\"tl-accept\">Accept all</button></div>";
    document.body.appendChild(b);
    document.getElementById("tl-reject").onclick = function () { write("denied"); close(); };
    document.getElementById("tl-accept").onclick = function () { write("granted"); close(); };
  }
  window.tinkerlabCookieSettings = open;

  function init() {
    if (!read()) open();
    document.addEventListener("click", function (e) {
      var t = e.target.closest && e.target.closest("[data-cookie-settings]");
      if (t) { e.preventDefault(); open(); }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
