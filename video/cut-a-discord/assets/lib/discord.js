/* Cut A only: helpers for the Discord desktop window (see discord.css). Deterministic: every value is a
   function of timeline time. Loaded once by index.html after squad.js. */
(function () {
  "use strict";
  var S = 1.3; // px per Discord dp at camera 1.0 (see discord.css)
  var B = 3; // window border (px)

  var ICON = {
    hash:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 3L8 21M16 3l-2 18M4 8.5h17M3 15.5h17"/></svg>',
    chev: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    check:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
    eye: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
    ext: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
    home: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v9a2.5 2.5 0 0 1-2.5 2.5H11l-4.6 3.6c-.5.4-1.4.1-1.4-.6V17h-.5A2.5 2.5 0 0 1 2 14.5z" transform="translate(1 0)"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
    mic: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="8.5" y="2" width="7" height="12" rx="3.5"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    phones:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 15v-3a8 8 0 0 1 16 0v3"/><rect x="3" y="14" width="5" height="7" rx="2" fill="currentColor"/><rect x="16" y="14" width="5" height="7" rx="2" fill="currentColor"/></svg>',
    gear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1" stroke-linecap="round"/></svg>',
    friends:
      '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="9" cy="8" r="4"/><path d="M1.5 20a7.5 7.5 0 0 1 15 0z"/><circle cx="17.5" cy="9" r="3"/><path d="M17 13.6a6 6 0 0 1 5.5 6.4H18a9 9 0 0 0-2.4-6.2c.4-.1.9-.2 1.4-.2z"/></svg>',
    thread:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 3L7.5 13M14 3l-1.5 10M4 6.5h12M3.5 10.5h11"/><path d="M13 15h8v6l-2.5-2H13z" fill="currentColor" stroke-linejoin="round"/></svg>',
    cal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4" stroke-linecap="round"/></svg>',
    at: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8" stroke-linecap="round"/></svg>',
    cursor:
      '<svg viewBox="0 0 30 42"><path d="M2 2v33l8.2-7.6 5.6 12.4 6.3-2.8-5.6-12.2H28z" fill="#111" stroke="#fff" stroke-width="3" stroke-linejoin="round"/></svg>',
  };

  function mount(root) {
    root.querySelectorAll("[data-dci]").forEach(function (el) {
      el.innerHTML = ICON[el.getAttribute("data-dci")] || "";
    });
  }

  // layout offset (dp) of el inside the window's .dc-ui (ignores transforms)
  function dp(el, ui) {
    var x = 0,
      y = 0,
      n = el;
    while (n && n !== ui) {
      x += n.offsetLeft;
      y += n.offsetTop;
      n = n.offsetParent;
    }
    return { x: x, y: y };
  }
  // world point of el (fx, fy = fraction of its box; dy = extra dp, e.g. a scrolled list's y; win = .dc-win)
  function at(win, el, fx, fy, dy, dx) {
    var ui = win.querySelector(".dc-ui");
    var p = dp(el, ui);
    return {
      x: win.offsetLeft + B + (p.x + el.offsetWidth * (fx === undefined ? 0.5 : fx) + (dx || 0)) * S,
      y: win.offsetTop + B + (p.y + el.offsetHeight * (fy === undefined ? 0.5 : fy) + (dy || 0)) * S,
    };
  }
  // world rect of el
  function rect(win, el, dy) {
    var a = at(win, el, 0, 0, dy),
      b = at(win, el, 1, 1, dy);
    return { x: a.x, y: a.y, w: b.x - a.x, h: b.y - a.y, cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2 };
  }

  // list y (dp) that puts el's bottom at the scroller's bottom (Discord keeps the newest message at the bottom)
  function bottomY(scroller, el, pad) {
    return scroller.clientHeight - (el.offsetTop + el.offsetHeight) - (pad === undefined ? 8 : pad);
  }
  // list y (dp) that puts el's top at the scroller's top
  function topY(el, pad) {
    return -(el.offsetTop - (pad === undefined ? 8 : pad));
  }

  // type text into el char by char (per s/char); returns the end time
  function type(tl, el, text, t0, per) {
    var o = { n: 0 };
    el.textContent = "";
    tl.fromTo(
      o,
      { n: 0 },
      {
        n: text.length,
        duration: text.length * per,
        ease: "none",
        onUpdate: function () {
          el.textContent = text.slice(0, Math.floor(o.n + 1e-6));
        },
      },
      t0,
    );
    return t0 + text.length * per;
  }

  // cursor travel on a 6 % arc (power3.inOut, 0.45 s) and press (0.88 in 0.06 s, release 0.10 s)
  function move(tl, cur, t0, a, b, dur) {
    var dx = b.x - a.x,
      dy = b.y - a.y;
    SQ.arc(tl, cur, t0, dur || 0.45, a, b, 0.06 * Math.sqrt(dx * dx + dy * dy), "power3.inOut");
  }
  function press(tl, cur, t0) {
    tl.to(cur, { scale: 0.88, duration: 0.06, ease: "power2.out" }, t0);
    tl.to(cur, { scale: 1, duration: 0.1, ease: "power2.out" }, t0 + 0.06);
  }
  // a Discord button darkening 10 % for 0.1 s on press
  function btnPress(tl, btn, t0) {
    var d = btn.querySelector(".dc-dim");
    if (!d) return;
    tl.fromTo(d, { opacity: 0 }, { opacity: 0.12, duration: 0.04, ease: "none" }, t0);
    tl.to(d, { opacity: 0, duration: 0.1, ease: "power1.out" }, t0 + 0.1);
  }
  // tick a checkbox / radio on the press frame
  function tick(tl, box, t0) {
    var on = box.querySelector(".on");
    tl.fromTo(on, { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.1, ease: "back.out(1.6)" }, t0);
  }
  function untick(tl, box, t0) {
    tl.to(box.querySelector(".on"), { opacity: 0, duration: 0.06, ease: "none" }, t0);
  }
  // blur swap between two stacked states
  function swap(tl, a, b, t0) {
    tl.to(a, { opacity: 0, filter: "blur(8px)", duration: 0.13, ease: "power2.in" }, t0);
    tl.fromTo(b, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.13, ease: "power2.out" }, t0 + 0.13);
  }
  // Discord message arrival: 2 frames, scale 0.92 -> 1 from the bottom-left
  function arrive(tl, el, t0) {
    gsap.set(el, { transformOrigin: "0% 100%" });
    SQ.pop(tl, el, t0);
  }

  window.DC = {
    S: S,
    ICON: ICON,
    mount: mount,
    at: at,
    rect: rect,
    bottomY: bottomY,
    topY: topY,
    type: type,
    move: move,
    press: press,
    btnPress: btnPress,
    tick: tick,
    untick: untick,
    swap: swap,
    arrive: arrive,
  };
})();
