/* Squad Mode film: shared helpers (both cuts). Loaded once by the root index.html, before any scene mounts.
   Everything here is deterministic: tweens on the scene's own paused timeline, no clocks, no randomness.
   SQ.mount(root) fills decorative SVG placeholders (status icons, tails, locks, arrows, event icons);
   the SQ.* motion helpers encode SPEC.md section 4 so every scene moves the same way. */
(function () {
  "use strict";
  var INK = "#111";

  var ICON = {
    // event icons, flat 2-colour, 96 x 96, ink on the card's colour block
    mic:
      '<svg viewBox="0 0 96 96"><rect x="34" y="8" width="28" height="46" rx="14" fill="#fff" stroke="#111" stroke-width="6"/>' +
      '<path d="M40 22h16M40 32h16M40 42h16" stroke="#111" stroke-width="4" stroke-linecap="round"/>' +
      '<path d="M24 44a24 24 0 0 0 48 0" fill="none" stroke="#111" stroke-width="6" stroke-linecap="round"/>' +
      '<path d="M48 68v14M34 86h28" stroke="#111" stroke-width="6" stroke-linecap="round"/></svg>',
    brush:
      '<svg viewBox="0 0 96 96"><path d="M70 10l16 16-34 34-16-16z" fill="#fff" stroke="#111" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M36 44l16 16-8 8c-6 6-16 6-22 0l-2-2c-6-6-6-16 0-22z" fill="#111"/>' +
      '<path d="M22 66c-4 8-8 12-14 16 10 2 22 0 28-6" fill="#111"/></svg>',
    hike:
      '<svg viewBox="0 0 96 96"><circle cx="70" cy="26" r="12" fill="#fff" stroke="#111" stroke-width="6"/>' +
      '<path d="M6 82l28-44 16 24 10-14 30 34z" fill="#fff" stroke="#111" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M26 50l8 6 6-6" fill="none" stroke="#111" stroke-width="5" stroke-linejoin="round"/></svg>',
    dice:
      '<svg viewBox="0 0 96 96"><rect x="8" y="30" width="44" height="44" rx="9" fill="#fff" stroke="#111" stroke-width="6" transform="rotate(-10 30 52)"/>' +
      '<rect x="46" y="18" width="40" height="40" rx="8" fill="#fff" stroke="#111" stroke-width="6" transform="rotate(12 66 38)"/>' +
      '<circle cx="22" cy="44" r="4.5" fill="#111"/><circle cx="30" cy="54" r="4.5" fill="#111"/><circle cx="38" cy="63" r="4.5" fill="#111"/>' +
      '<circle cx="60" cy="30" r="4.5" fill="#111"/><circle cx="73" cy="46" r="4.5" fill="#111"/></svg>',
    // status bar (iOS), currentColor
    signal:
      '<svg viewBox="0 0 18 12" fill="currentColor"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/>' +
      '<rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>',
    wifi:
      '<svg viewBox="0 0 16 12" fill="currentColor"><path d="M8 2.3c2.4 0 4.6.9 6.2 2.5l1.3-1.3C13.5 1.5 10.9.4 8 .4S2.5 1.5.5 3.5l1.3 1.3C3.4 3.2 5.6 2.3 8 2.3z"/>' +
      '<path d="M8 5.8c1.5 0 2.8.6 3.8 1.5l1.3-1.3C11.8 4.7 10 4 8 4s-3.8.7-5.1 2l1.3 1.3c1-.9 2.3-1.5 3.8-1.5z"/><path d="M8 9.2c.6 0 1.1.2 1.5.6L8 11.3 6.5 9.8c.4-.4.9-.6 1.5-.6z"/></svg>',
    batt:
      '<svg class="batt" viewBox="0 0 30 13"><rect x="0.5" y="0.5" width="26" height="12" rx="3.5" fill="none" stroke="currentColor" stroke-opacity=".4"/>' +
      '<rect x="2" y="2" width="19.5" height="9" rx="2" fill="currentColor"/><path d="M28 4.5v4c.8-.3 1.3-1.1 1.3-2s-.5-1.7-1.3-2z" fill="currentColor" fill-opacity=".4"/></svg>',
    back: '<svg viewBox="0 0 12 21"><path d="M10 2L2 10.5 10 19" fill="none" stroke="#0a84ff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    // iOS curl tail (Track 1 reference path), anchored at the bubble's bottom-left
    tail: '<svg class="im-tail" viewBox="-6 -18 24 18"><path d="M12 -16q-5 13-18 16q13 2 22-6z"/></svg>',
    // call buttons
    phone:
      '<svg viewBox="0 0 24 24" fill="#fff"><path d="M6.6 10.8a15.2 15.2 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>',
    hangup:
      '<svg viewBox="0 0 24 24" fill="#fff"><path transform="rotate(135 12 12)" d="M6.6 10.8a15.2 15.2 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>',
    speaker:
      '<svg viewBox="0 0 24 24" fill="#fff"><path d="M3 9v6h4l5 4V5L7 9z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18 6a8.5 8.5 0 0 1 0 12" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>',
    mute:
      '<svg viewBox="0 0 24 24"><rect x="9" y="3" width="6" height="11" rx="3" fill="#fff"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>',
    // lock: body + a shackle that GSAP lifts (y -6, rotate 30 about its left post)
    lock:
      '<svg class="sq-lockglyph" viewBox="0 0 24 28"><path class="shackle" d="M6 13V8a6 6 0 0 1 12 0v5" fill="none" stroke="#111" stroke-width="3.2" stroke-linecap="round"/>' +
      '<rect x="2" y="12" width="20" height="15" rx="3" fill="#111"/><circle cx="12" cy="19" r="2.4" fill="#fff4e0"/></svg>',
    arrow:
      '<svg class="sq-arrow" viewBox="0 0 18 14"><path d="M1 7h15M10 1.5L16 7l-6 5.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    ring: '<svg class="sq-ring"><rect class="ink" pathLength="100"/><rect class="gold" pathLength="100"/></svg>',
  };

  function mount(root) {
    root.querySelectorAll("[data-sq]").forEach(function (el) {
      var k = el.getAttribute("data-sq");
      if (k === "status") {
        el.innerHTML = ICON.signal + ICON.wifi + ICON.batt;
      } else if (ICON[k]) {
        // swap the placeholder for the SVG, keeping its id and inline style
        var t = document.createElement("div");
        t.innerHTML = ICON[k];
        var svg = t.firstChild;
        if (el.id) svg.id = el.id;
        if (el.getAttribute("style")) svg.setAttribute("style", el.getAttribute("style"));
        el.parentNode.replaceChild(svg, el);
      }
    });
    root.querySelectorAll("[data-ico]").forEach(function (el) {
      el.innerHTML = ICON[el.getAttribute("data-ico")] || "";
    });
  }

  // camera: put world point (wx, wy) at screen point (sx, sy) at scale s
  function frame(s, wx, wy, sx, sy) {
    sx = sx === undefined ? 960 : sx;
    sy = sy === undefined ? 540 : sy;
    return { scale: s, x: sx - wx * s, y: sy - wy * s };
  }
  function cam(tl, el, at, f, dur, ease) {
    var v = { scale: f.scale, x: f.x, y: f.y, duration: dur, ease: ease || "power3.inOut" };
    tl.to(el, v, at);
  }
  function camSet(tl, el, f) {
    gsap.set(el, { scale: f.scale, x: f.x, y: f.y });
    tl.set(el, { scale: f.scale, x: f.x, y: f.y }, 0);
  }

  // chat bubble arrival: 2 frames, scale 0.92 -> 1 from the sender's corner
  function pop(tl, el, at) {
    tl.fromTo(el, { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.067, ease: "none" }, at);
  }
  // sticker land: back.out(1.0) scale 0.6 -> 1 in 0.30 s, opacity in the first 0.08 s
  function land(tl, el, at, extra) {
    var from = { scale: 0.6 };
    var to = { scale: 1, duration: 0.3, ease: "back.out(1.0)" };
    if (extra) {
      Object.keys(extra.from || {}).forEach(function (k) { from[k] = extra.from[k]; });
      Object.keys(extra.to || {}).forEach(function (k) { to[k] = extra.to[k]; });
    }
    tl.fromTo(el, from, to, at);
    tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.08, ease: "none" }, at);
  }
  // super slam: power3.in, scale 1.35 -> 1, blur 8 -> 0 in 0.18 s, then dead still
  function slam(tl, el, at) {
    tl.fromTo(
      el,
      { opacity: 0, scale: 1.35, filter: "blur(8px)" },
      { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.18, ease: "power3.in" },
      at,
    );
  }
  // exit: opacity -> 0 + blur 0 -> 6 px, power2.in
  function exit(tl, el, at, dur) {
    tl.fromTo(
      el,
      { opacity: 1, filter: "blur(0px)" },
      { opacity: 0, filter: "blur(6px)", duration: dur || 0.2, ease: "power2.in", immediateRender: false },
      at,
    );
  }

  // split an element's text nodes into <span class="w"> words (keeps child elements like <em>)
  function words(el) {
    var out = [];
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (c) {
        if (c.nodeType === 3) {
          var parts = c.textContent.split(/(\s+)/);
          var frag = document.createDocumentFragment();
          parts.forEach(function (p) {
            if (!p) return;
            if (/^\s+$/.test(p)) {
              frag.appendChild(document.createTextNode(p));
            } else {
              var s = document.createElement("span");
              s.className = "w";
              s.textContent = p;
              frag.appendChild(s);
              out.push(s);
            }
          });
          node.replaceChild(frag, c);
        } else if (c.nodeType === 1 && !c.classList.contains("w")) {
          walk(c);
        }
      });
    })(el);
    return out;
  }
  // title words: blur 6 -> 0 + opacity, 0.13 s each, gap apart, no translate
  function blurWords(tl, ws, at, gap, dur) {
    ws.forEach(function (w, i) {
      tl.fromTo(
        w,
        { opacity: 0, filter: "blur(6px)" },
        { opacity: 1, filter: "blur(0px)", duration: dur || 0.13, ease: "power2.out" },
        at + i * (gap === undefined ? 0.067 : gap),
      );
    });
  }
  // sub line: per word ink 25% -> 100%
  function inkWords(tl, ws, at, gap) {
    ws.forEach(function (w, i) {
      tl.fromTo(
        w,
        { color: "rgba(17,17,17,0.25)" },
        { color: "rgba(17,17,17,1)", duration: 0.12, ease: "power1.out" },
        at + i * (gap || 0.07),
      );
    });
  }

  // focus ring: dashoffset 100 -> 0 in 0.35 s power2.out; leaves with opacity in 0.15 s
  function ring(tl, svg, at) {
    tl.fromTo(svg, { opacity: 0 }, { opacity: 1, duration: 0.01 }, at);
    tl.fromTo(
      svg.querySelectorAll("rect"),
      { strokeDashoffset: 100 },
      { strokeDashoffset: 0, duration: 0.35, ease: "power2.out" },
      at,
    );
  }
  function ringOut(tl, svg, at) {
    tl.to(svg, { opacity: 0, duration: 0.15, ease: "power1.in" }, at);
  }

  // typing dots: opacity wave 0.35 -> 1, period 0.9 s, 0.15 s phase per dot, finite repeats
  function dots(tl, dotEls, start, end) {
    Array.prototype.forEach.call(dotEls, function (d, i) {
      var t0 = start + i * 0.15;
      var n = Math.max(0, Math.floor((end - t0) / 0.45) - 1);
      tl.fromTo(
        d,
        { opacity: 0.35 },
        { opacity: 1, duration: 0.45, ease: "sine.inOut", yoyo: true, repeat: n },
        t0,
      );
    });
  }

  // lock shackle: open lifts 6 px and rotates 30 deg about its left post; close reverses
  function lockOpen(tl, glyph, at, dur) {
    var s = glyph.querySelector(".shackle");
    tl.fromTo(
      s,
      { y: 0, rotation: 0, svgOrigin: "6 13" },
      { y: -6, rotation: 30, svgOrigin: "6 13", duration: dur || 0.25, ease: "back.out(1.4)" },
      at,
    );
  }
  function lockClose(tl, glyph, at, dur) {
    var s = glyph.querySelector(".shackle");
    tl.fromTo(
      s,
      { y: -6, rotation: 30, svgOrigin: "6 13" },
      { y: 0, rotation: 0, svgOrigin: "6 13", duration: dur || 0.18, ease: "power3.in" },
      at,
    );
  }
  function lockSetOpen(glyph) {
    gsap.set(glyph.querySelector(".shackle"), { y: -6, rotation: 30, svgOrigin: "6 13" });
  }

  // number count-up driven by the timeline (seek-safe)
  function count(tl, el, from, to, at, dur, ease, fmt) {
    var o = { v: from };
    fmt = fmt || function (v) { return String(Math.round(v)); };
    el.textContent = fmt(from);
    tl.fromTo(
      o,
      { v: from },
      {
        v: to,
        duration: dur,
        ease: ease || "power2.out",
        onUpdate: function () { el.textContent = fmt(o.v); },
      },
      at,
    );
  }

  // status clock slot roll: each character rolls through its own strip (built from `seqs`)
  function rollClock(el, seqs) {
    el.innerHTML = "";
    return seqs.map(function (seq) {
      if (typeof seq === "string") {
        el.appendChild(document.createTextNode(seq));
        return null;
      }
      var box = document.createElement("span");
      box.className = "roll";
      var strip = document.createElement("span");
      strip.style.display = "block";
      seq.forEach(function (ch) {
        var c = document.createElement("span");
        c.textContent = ch === " " ? "\u00a0" : ch;
        c.style.display = "block";
        strip.appendChild(c);
      });
      box.appendChild(strip);
      el.appendChild(box);
      return { strip: strip, n: seq.length };
    }).filter(Boolean);
  }
  function roll(tl, strips, at, dur, lineH) {
    strips.forEach(function (s) {
      tl.fromTo(
        s.strip,
        { y: 0 },
        { y: -(s.n - 1) * lineH, duration: dur, ease: "power1.inOut" },
        at,
      );
    });
  }

  // super: 52 px unless the longest line would make the box wider than `max` (SPEC: <= 680 px, 2 lines)
  function fitSuper(el, max) {
    max = max || 680;
    var fs = 52;
    el.style.fontSize = fs + "px";
    while (el.offsetWidth > max && fs > 32) {
      fs -= 1;
      el.style.fontSize = fs + "px";
    }
    return fs;
  }

  // layout offset of el inside ancestor (ignores transforms; read once at build)
  function offset(el, ancestor) {
    var x = 0, y = 0, n = el;
    while (n && n !== ancestor) {
      x += n.offsetLeft;
      y += n.offsetTop;
      n = n.offsetParent;
    }
    return { x: x, y: y };
  }
  // fly el (GSAP x/y) from a to b on an arc that bulges `lift` px upward (12 % of the distance by default)
  function arc(tl, el, at, dur, a, b, lift, ease) {
    var dx = b.x - a.x, dy = b.y - a.y;
    lift = lift === undefined ? 0.12 * Math.sqrt(dx * dx + dy * dy) : lift;
    var cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2 - lift * 2;
    var o = { p: 0 };
    tl.fromTo(
      o,
      { p: 0 },
      {
        p: 1,
        duration: dur,
        ease: ease || "power2.inOut",
        onUpdate: function () {
          var p = o.p, q = 1 - p;
          gsap.set(el, { x: q * q * a.x + 2 * q * p * cx + p * p * b.x, y: q * q * a.y + 2 * q * p * cy + p * p * b.y });
        },
      },
      at,
    );
  }

  window.SQ = {
    offset: offset,
    arc: arc,
    fitSuper: fitSuper,
    ICON: ICON,
    mount: mount,
    frame: frame,
    cam: cam,
    camSet: camSet,
    pop: pop,
    land: land,
    slam: slam,
    exit: exit,
    words: words,
    blurWords: blurWords,
    inkWords: inkWords,
    ring: ring,
    ringOut: ringOut,
    dots: dots,
    lockOpen: lockOpen,
    lockClose: lockClose,
    lockSetOpen: lockSetOpen,
    count: count,
    rollClock: rollClock,
    roll: roll,
    INK: INK,
  };
})();
