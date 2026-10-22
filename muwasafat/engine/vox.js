// vox.js — primitives for editorial "paper-collage" explainer motion graphics
// (Vox / Johnny Harris / NYT-collage family). Defaults are MEASURED from the
// reference videos — see docs/ for where each number comes from.
//
// Model: two paused GSAP timelines, seeked per frame by render.mjs
//   c.tl   — CONTENT clock (text, highlights, strokes, pops). Optionally posterised
//            to `step` fps (10 = kinetic short, 15 = "on twos" at 30) for a hand-made feel.
//   c.ctl  — CAMERA clock (camera moves, page wipes, scene cuts, live tickers). Always smooth.
// All randomness is seeded => every render is identical.

const gsap = window.gsap;
if (!gsap) throw new Error('load engine/lib/gsap.min.js before vox.js');

// ------------------------------------------------------------------ utils
export function rng(seed = 1) {           // mulberry32
  let a = seed >>> 0;
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
export const $ = (q, root = document) => (typeof q === 'string' ? root.querySelector(q) : q);
export const $$ = (q, root = document) => (typeof q === 'string' ? [...root.querySelectorAll(q)] : q instanceof Element ? [q] : [...q].flatMap(x => (typeof x === 'string' ? [...root.querySelectorAll(x)] : [x])));
const svgNS = 'http://www.w3.org/2000/svg';
const svgURL = s => `url("data:image/svg+xml;charset=utf-8,${encodeURIComponent(s)}")`;
/** frames -> seconds (reference timings are quoted in 30 fps frames unless noted) */
export const F = (n, fps = 30) => n / fps;
/** CSS-style cubic-bezier easing usable as a GSAP ease */
export function bezier(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const X = t => ((ax * t + bx) * t + cx) * t, Y = t => ((ay * t + by) * t + cy) * t;
  return x => { if (x <= 0) return 0; if (x >= 1) return 1; let a = 0, b = 1, t = x; for (let i = 0; i < 40; i++) { t = (a + b) / 2; X(t) < x ? (a = t) : (b = t); } return Y(t); };
}
/** measured eases (docs/05-motion.md) */
export const EASE = {
  hlBurst: bezier(0.9, 0.1, 0, 0.9),   // v1 highlighter "land - burst - settle"
  typeCount: bezier(0.9, 0, 0.3, 0.8), // v1 headline typing: chars revealed on an ease-in-out count
  ride: bezier(0.5, 0.05, 0.4, 1),     // v2 chart line + year rider
};

// palette presets (measured, see docs/02-color.md)
export const PALETTES = {
  explainer: { paper: '#ece6dc', grid: '#ddd6cb', ink: '#19140d', red: '#e1361b', yellow: '#f5c713', mute: '#857c72', card: '#f4efe8' }, // v2 debt
  collage:   { paper: '#dddfd8', grid: '#979991', ink: '#0a0a0a', red: '#c04343', outline: '#aa4850', pen: '#a8434c', yellow: '#fff34f', mute: '#73746f', card: '#f3f1ec' }, // v1 headline collage
  story:     { paper: '#eceae7', grid: '#dad6d0', ink: '#0a0605', red: '#c8322b', yellow: '#f9c432', mute: '#6f6a63', card: '#f6f3ef', blue: '#3036d5' }, // v3 map story
  notes:     { paper: '#efeee6', grid: 'rgba(110,190,185,.24)', ink: '#020300', red: '#e5383b', yellow: '#e9c510', mute: '#666', card: '#fff', marker: '#f6c54a' }, // v5 kinetic
  black:     { paper: '#050505', grid: 'rgba(0,0,0,0)', ink: '#f2f2ef', red: '#e1361b', yellow: '#f5c713', mute: '#817f7d', card: '#1b1a17' }, // v2 finale
};

// ------------------------------------------------------------------ textures (static — references never animate paper grain)
export const textures = {
  crumpled({ base = '#e9e7e2', seed = 3, freq = 0.0035, depth = 5, contrast = 0.6, w = 1920, h = 1080 } = {}) {
    const s = contrast, i = 1 - s * 0.85;
    return svgURL(`<svg xmlns="${svgNS}" width="${w}" height="${h}">
      <filter id="c" x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" stitchTiles="stitch" baseFrequency="${freq}" numOctaves="6" seed="${seed}" result="n"/>
        <feDiffuseLighting in="n" surfaceScale="${depth}" lighting-color="#fff" diffuseConstant="1.15" result="l"><feDistantLight azimuth="225" elevation="42"/></feDiffuseLighting>
        <feColorMatrix in="l" type="saturate" values="0" result="g"/>
        <feComponentTransfer in="g" result="g2"><feFuncR type="linear" slope="${s}" intercept="${i}"/><feFuncG type="linear" slope="${s}" intercept="${i}"/><feFuncB type="linear" slope="${s}" intercept="${i}"/></feComponentTransfer>
        <feFlood flood-color="${base}"/><feBlend in2="g2" mode="multiply"/>
      </filter><rect width="100%" height="100%" filter="url(#c)"/></svg>`);
  },
  fibre({ seed = 5, w = 1920, h = 1080, amount = 0.10 } = {}) {
    return svgURL(`<svg xmlns="${svgNS}" width="${w}" height="${h}">
      <filter id="m" x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" stitchTiles="stitch" baseFrequency="0.005" numOctaves="3" seed="${seed}" result="lo"/>
        <feTurbulence type="fractalNoise" stitchTiles="stitch" baseFrequency="0.85" numOctaves="2" seed="${seed + 1}" result="hi"/>
        <feBlend in="lo" in2="hi" mode="multiply" result="n"/>
        <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.32  0 0 0 0 0.27  0 0 0 0 0.2  0 0 0 ${amount * 5} -${amount * 1.9}"/>
      </filter><rect width="100%" height="100%" filter="url(#m)"/></svg>`);
  },
  specks({ seed = 8, w = 1920, h = 1080, n = 70, light = false } = {}) {
    const r = rng(seed); let s = '';
    for (let i = 0; i < n; i++) { const x = r() * w, y = r() * h, rr = 0.5 + r() * 1.6; s += `<ellipse cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" rx="${rr.toFixed(1)}" ry="${(rr * (0.5 + r())).toFixed(1)}" opacity="${(0.12 + r() * 0.3).toFixed(2)}"/>`; }
    return svgURL(`<svg xmlns="${svgNS}" width="${w}" height="${h}"><g fill="${light ? '#fff' : '#3a3128'}">${s}</g></svg>`);
  },
  // highlighter swatch. kind: 'block' | 'marker' (streaky) | 'torn' (ragged opaque) | 'brush' (dry brush, gaps)
  marker({ kind = 'marker', color = '#f2e030', seed = 1, w = 600, h = 80, alpha = 0.92, radius = 8 } = {}) {
    const r = rng(seed); let body = '';
    if (kind === 'block') body = `<rect x="0" y="0" width="${w}" height="${h}" rx="${Math.min(radius, h / 4)}" fill="${color}" fill-opacity="${alpha}"/>`;
    else if (kind === 'torn') body = `<rect x="5" y="5" width="${w - 10}" height="${h - 10}" fill="${color}" fill-opacity="${alpha}" filter="url(#t)"/>`;
    else {
      const dry = kind === 'brush', n = dry ? 46 : 26;
      for (let i = 0; i < n; i++) {
        const y = h * (0.12 + 0.76 * (i / (n - 1))) + (r() - 0.5) * h * 0.04, sw = h * (dry ? 0.02 + r() * 0.05 : 0.06 + r() * 0.05);
        const x0 = r() * w * (dry ? 0.06 : 0.035), x1 = w - r() * w * (dry ? 0.08 : 0.04), wob = (r() - 0.5) * h * 0.06;
        const op = dry ? 0.35 + r() * 0.65 : 0.8 + r() * 0.2;
        body += `<path d="M${x0.toFixed(1)} ${y.toFixed(1)} Q${(w / 2).toFixed(1)} ${(y + wob).toFixed(1)} ${x1.toFixed(1)} ${(y - wob * 0.5).toFixed(1)}" stroke="${color}" stroke-opacity="${(op * alpha).toFixed(2)}" stroke-width="${sw.toFixed(1)}" stroke-linecap="round" fill="none"/>`;
      }
    }
    return svgURL(`<svg xmlns="${svgNS}" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <filter id="t" x="-5%" y="-20%" width="110%" height="140%"><feTurbulence type="fractalNoise" stitchTiles="stitch" baseFrequency="0.08 0.3" numOctaves="3" seed="${seed}"/><feDisplacementMap in="SourceGraphic" scale="${Math.max(5, h * 0.09)}" xChannelSelector="R" yChannelSelector="G"/></filter>
      ${body}</svg>`);
  },
};

// ------------------------------------------------------------------ composition
export class Comp {
  /**
   * @param o.paper    'graph' | 'dots' | 'plain' | 'crumpled' | 'lined'
   * @param o.palette  key of PALETTES or object (sets CSS vars --paper --ink --red --yellow --mute --card)
   * @param o.gridGap  graph/dot pitch in px at 1080p (45 debt, 42 story, 94 kinetic short)
   * @param o.vignette 0..1 corner darkening (0.25 debt, 0.35 kinetic, 0.6 newsprint, 0 story)
   * @param o.step     posterise the CONTENT clock to N fps (15 = on twos, 10 = kinetic short), null = smooth
   * @param o.post     ffmpeg film FX applied by render.mjs: { grain, rgb, blur }
   */
  constructor({ width = 1920, height = 1080, paper = 'graph', palette = 'explainer', gridGap = 45, dotGap, vignette = 0.25, fibre = 0.08, specks = 60, crumple = {}, step = null, post = {}, seed = 1, stage = '#stage' } = {}) {
    Object.assign(this, { width, height, seed, step });
    this.u = Math.min(width, height) / 1080;     // 1 unit = 1 px of the 1080-short-side reference
    this.pal = typeof palette === 'string' ? { ...PALETTES[palette] } : { ...PALETTES.explainer, ...palette };
    this.post = { grain: 0, rgb: 0, blur: 0, ...post };
    this.clocks = [];
    this.tl = this.clock(step);     // content clock
    this.ctl = this.clock(null);    // camera clock (smooth)
    const st = this.stage = $(stage);
    st.classList.add('vox-stage');
    Object.assign(st.style, { width: width + 'px', height: height + 'px' });
    for (const [k, v] of Object.entries(this.pal)) st.style.setProperty('--' + k, v);
    // stage > cam > [ paper, pattern, world(your content) ] ; overlays (fx, vignette, hud) above cam
    const kids = [...st.childNodes];
    this.rig = this._div('rig', st);              // hand-held layer: drift / shake only
    this.cam = this._div('cam', this.rig);        // camera layer: push / pan / roll / rack focus
    this.paperEl = this._div('layer vox-paper', this.cam);
    this.patternEl = this._div('layer vox-pattern', this.cam);
    this.world = this._div('layer world', this.cam);
    kids.forEach(n => (n.nodeType === 1 && n.classList.contains('hud') ? null : this.world.appendChild(n)));
    [this.paperEl, this.patternEl].forEach(l => (l.style.inset = '-25%'));  // bleed: camera moves never show an edge
    this.fx = this._div('vox-overlay vox-fx', st);
    this.vig = this._div('vox-overlay vox-vignette', st);
    this.hud = this._div('vox-overlay vox-hud', st);                       // persistent widgets: never blurred / wiped
    kids.forEach(n => n.nodeType === 1 && n.classList.contains('hud') && this.hud.appendChild(n));
    this.setPaper(paper, { gridGap, dotGap, fibre, specks, crumple });
    this.setVignette(vignette);
  }
  /** grow the paper so a tall/wide world can be explored by camera tilts (px beyond the frame edges) */
  extend({ top = 0, right = 0, bottom = 0, left = 0 } = {}) {
    [this.paperEl, this.patternEl].forEach(l => Object.assign(l.style, { top: -(top || 270) + 'px', right: -(right || 480) + 'px', bottom: -(bottom || 270) + 'px', left: -(left || 480) + 'px' }));
  }
  _div(cls, parent) { const d = document.createElement('div'); d.className = cls; parent.appendChild(d); return d; }

  /** paper base + pattern. Can be applied to any element (e.g. a .sheet) via `target` */
  setPaper(kind, { gridGap = 45, dotGap, fibre = 0.08, specks = 60, base, crumple = {}, target, pattern: patTarget } = {}) {
    const W = Math.round(this.width * 1.5), H = Math.round(this.height * 1.5), p = this.pal, g = gridGap * this.u;
    const layers = [];
    if (specks) layers.push(textures.specks({ w: W, h: H, n: Math.round(specks * 2.2), light: this._isDark(base || p.paper), seed: this.seed + 8 }));
    if (fibre) layers.push(textures.fibre({ w: W, h: H, amount: fibre, seed: this.seed + 5 }));
    if (kind === 'crumpled') layers.push(textures.crumpled({ w: W, h: H, base: base || p.paper, seed: this.seed + 3, ...crumple }));
    const bg = layers.join(',') + (layers.length ? ',' : '') + (base || p.paper);
    const pat = this._pattern(kind, g, dotGap ? dotGap.map(v => v * this.u) : null);
    if (target) {
      const el = $(target), n = pat.img === 'none' ? 0 : pat.img.split('gradient(').length - 1;
      el.style.background = (n ? pat.img + ',' : '') + bg;
      el.style.backgroundSize = [...Array(n).fill(pat.size), ...layers.map(() => 'auto')].join(',') || 'auto';
      el.style.backgroundPosition = 'center';
      return;
    }
    this.paperEl.style.background = bg;
    Object.assign(this.patternEl.style, { backgroundImage: pat.img, backgroundSize: pat.size, backgroundPosition: 'center' });
  }
  _pattern(kind, g, dg) {
    const p = this.pal, lw = Math.max(1, 1.4 * this.u);
    if (kind === 'graph') return { img: `linear-gradient(${p.grid} ${lw}px, transparent ${lw}px), linear-gradient(90deg, ${p.grid} ${lw}px, transparent ${lw}px)`, size: `${g}px ${g}px` };
    if (kind === 'dots') { const [dx, dy] = dg || [g * 0.62, g * 0.62]; return { img: `radial-gradient(circle, ${p.grid} ${1.6 * this.u}px, transparent ${2.3 * this.u}px)`, size: `${dx}px ${dy}px` }; }
    if (kind === 'lined') return { img: `linear-gradient(transparent ${g - 3}px, rgba(110,140,150,.45) ${g - 3}px, rgba(110,140,150,.45) ${g}px)`, size: `100% ${g}px` };
    return { img: 'none', size: 'auto' };
  }
  _isDark(c) { const m = /^#?([0-9a-f]{6})$/i.exec(c || ''); if (!m) return false; const n = parseInt(m[1], 16); return ((n >> 16) + ((n >> 8) & 255) + (n & 255)) / 3 < 80; }
  /** corner darkening: flat to ~45 % radius, then falls off (measured v2/v5) */
  setVignette(v, tint = '60,42,25') { this.vig.style.background = v ? `radial-gradient(ellipse 72% 72% at 50% 50%, rgba(0,0,0,0) 45%, rgba(${tint},${(v * 0.5).toFixed(3)}) 75%, rgba(${tint},${Math.min(0.95, v * 1.3).toFixed(3)}) 100%)` : 'none'; }

  // finish: wait fonts + images, expose seek API for render.mjs (and ?play / ?t= preview)
  async ready(duration) {
    await document.fonts.ready;
    await Promise.all([...document.images].map(i => i.decode().catch(() => {})));
    this.duration = duration ?? Math.max(...this.clocks.map(c => c.tl.duration()));
    window.__comp = { ready: true, width: this.width, height: this.height, duration: this.duration, post: this.post, seek: t => this.seek(t) };
    const q = new URLSearchParams(location.search);
    this.seek(+(q.get('t') || 0));
    if (q.has('play')) { const t0 = performance.now(); const loop = () => { this.seek(((performance.now() - t0) / 1000) % this.duration); requestAnimationFrame(loop); }; loop(); }
  }
  /** extra clock posterised to `fps` (null = smooth). v1 uses 3: elements 15, typing 30, camera 60. */
  clock(fps) { const tl = gsap.timeline({ paused: true }); this.clocks.push({ tl, fps }); return tl; }
  seek(t) { for (const { tl, fps } of this.clocks) tl.time(fps ? Math.floor(t * fps + 1e-6) / fps : t, false); }
  /** add to the content clock at t */
  at(t, anim) { this.tl.add(anim.tl || anim, t); return anim; }
  /** add to the camera clock at t (camera moves, wipes, tickers) */
  camAt(t, anim) { this.ctl.add(anim.tl || anim, t); return anim; }

  // ---------------------------------------------------------- scenes
  show(sel, t) { this.ctl.set($$(sel), { visibility: 'visible' }, t); }
  hide(sel, t) { this.ctl.set($$(sel), { visibility: 'hidden' }, t); }
  /** hard cut: hide `from`, show `to` at t (cut inside a VO pause; new paper stays empty ~0.17 s) */
  cut(from, to, t) { if (from) this.hide(from, t); this.show(to, t); }

  // ---------------------------------------------------------- text splitting
  split(sel) {
    const el = $(sel); if (el._chars) return el._chars;
    const chars = [];
    const walk = node => [...node.childNodes].forEach(n => {
      if (n.nodeType === 3) {
        const frag = document.createDocumentFragment();
        n.textContent.split(/(\s+)/).forEach(part => {
          if (!part) return;
          if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(' ')); return; }
          const w = document.createElement('span'); w.className = 'w';
          [...part].forEach(ch => { const s = document.createElement('span'); s.className = 'ch'; s.textContent = ch; w.appendChild(s); chars.push(s); });
          frag.appendChild(w);
        });
        n.replaceWith(frag);
      } else if (n.nodeType === 1 && !n.classList.contains('hl-mark')) walk(n);
    });
    walk(el); el._chars = chars; return chars;
  }
  words(sel) { this.split(sel); return $$('.w', $(sel)); }

  // ---------------------------------------------------------- text reveals
  /**
   * Stepped typewriter, chars appear instantly in their final layout slot (no reflow, no cursor).
   * cps: 24 headline (v1), 28-30 kicker (v2), 12 slow data label (v3), 22 gloss.
   * ghost: new char shows at 45 % grey for one step first (v3 years/captions).
   */
  /**
   * `dur` + `curve`: reveal-count follows an ease over a fixed duration instead of a constant rate
   *   (v1 headline: 50 chars, dur 1.75, curve EASE.typeCount — slow start, whole words mid-line, slow last word).
   * `fade`: per-glyph fade-in seconds (v1: 0.17 power2.out); 0 = instant.
   */
  typeOn(sel, { cps = 26, ghost = false, jitter = 0, dur, curve, fade = 0 } = {}) {
    const chars = this.split(sel), tl = gsap.timeline(), r = rng(this.seed + chars.length), N = chars.length;
    gsap.set(chars, { opacity: 0 });
    const inv = y => { let a = 0, b = 1; for (let i = 0; i < 30; i++) { const m = (a + b) / 2; (gsap.parseEase(curve)(m) < y) ? (a = m) : (b = m); } return a; };
    let t = 0;
    chars.forEach((ch, i) => {
      if (dur && curve) t = dur * inv((i + 0.5) / N);
      if (ghost) tl.set(ch, { opacity: 0.45 }, t).set(ch, { opacity: 1 }, t + 1 / cps);
      else if (fade) tl.fromTo(ch, { opacity: 0.4 }, { opacity: 1, duration: fade, ease: 'power2.out', immediateRender: false }, t);
      else tl.set(ch, { opacity: 1 }, t);
      if (!(dur && curve)) t += (1 / cps) * (1 + (r() - 0.5) * jitter);
    });
    return tl;
  }
  /** remove chars right->left (v3 "1963" exit, ~30 cps) */
  unType(sel, { cps = 30 } = {}) {
    const chars = this.split(sel).slice().reverse(), tl = gsap.timeline();
    chars.forEach((ch, i) => tl.set(ch, { opacity: 0 }, i / cps));
    return tl;
  }
  /**
   * Spoken-line word reveal (v2): each word opacity 0->1, y +8 -> 0, blur 3px -> 0, 0.1-0.13 s power2.out.
   * Pass `times` (absolute seconds per word, from the VO) to lock to narration; else fixed stagger.
   */
  wordsIn(sel, { times, stagger = 0.2, dur = 0.12, y = 8, blur = 3, ease = 'power2.out' } = {}) {
    const ws = this.words(sel), tl = gsap.timeline();
    gsap.set(ws, { opacity: 0 });
    ws.forEach((w, i) => tl.fromTo(w, { opacity: 0, y: y * this.u, filter: `blur(${blur}px)` }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: dur, ease }, times ? times[i] - times[0] : i * stagger));
    return tl;
  }
  /**
   * Display caps rise from a mask just below the baseline (v2: THE INTEREST, $40 TRILLION, FUTURE):
   * back.out(1.7), 0.30 s per glyph, 0.028 s stagger, ~10 % overshoot. Mask needs .rise-mask on the element.
   */
  charRise(sel, { stagger = 0.028, dur = 0.3, ease = 'back.out(1.7)' } = {}) {
    const el = $(sel), chars = this.split(el);
    el.classList.add('rise-mask');
    return gsap.timeline().fromTo(chars, { yPercent: 112 }, { yPercent: 0, duration: dur, ease, stagger });
  }
  /** per-char fade grey -> ink (v3 script years "1948"/"1965": 0.1 s each, 0.165 s apart) */
  charFade(sel, { stagger = 0.165, dur = 0.1, from = '#8a8580' } = {}) {
    const chars = this.split(sel);
    gsap.set(chars, { opacity: 0 });
    return gsap.timeline().fromTo(chars, { opacity: 0, color: from }, { opacity: 1, color: 'var(--ink)', duration: dur, ease: 'none', stagger });
  }
  /**
   * Kinetic-short typing (v5). Each letter pops from the baseline: scale 0.15 -> 0.7 -> 1.12 -> 1.03 -> 1 per 0.1 s,
   * always opaque. The whole line slides from +W/2 to rest with expo.out 1.0 s. Line takes `dur` regardless of length.
   * Use with Comp({ step: 10 }).
   */
  typePop(sel, { dur = 0.6, slide = true, pop = [0.15, 0.7, 1.12, 1.03, 1], stepDur = 0.1 } = {}) {
    const el = $(sel), chars = this.split(el), tl = gsap.timeline();
    gsap.set(chars, { scale: 0, transformOrigin: '50% 85%' });
    if (slide) tl.fromTo(el, { x: el.offsetWidth / 2, y: 8 * this.u }, { x: 0, y: 0, duration: 1.0, ease: 'expo.out' }, 0);
    chars.forEach((c, i) => tl.to(c, { keyframes: pop.map(s => ({ scale: s, duration: stepDur, ease: 'none' })) }, 0.05 + i * (dur / chars.length)));
    return tl;
  }
  /** instant cut-in (1 frame) */
  cutIn(sel) { return gsap.timeline().fromTo($$(sel), { opacity: 0 }, { opacity: 1, duration: 0.001, immediateRender: true }); }

  // ---------------------------------------------------------- highlighter
  /**
   * Highlighter mark per line box, wiped L->R line after line. Presets (measured):
   *  'pill'     v2: flat rounded rect per word, -1.5 deg, 0.13 s power2.out, ~0.1 s after the word lands
   *  'low'      v3: sits low (from 45 % cap height to 25 % below baseline), runs past the end, 0.35 s power2.out
   *  'marker'   v4 notebook: streaky, low, overshoot right, 0.63-0.79 s/line LINEAR, 0.25 s gap
   *  'multiply' v4 newsprint: flat over text in multiply, ~1.1 s sine.out
   *  'headline' v1: ragged flat band, multiply under text, 1.47 s "land-burst-settle" curve (EASE.hlBurst)
   *  'torn'     v4 NETFLIX: opaque ragged block, +0.6 deg, 0.92 s sine.out
   *  'brush'    v4 Vox / v3 headline: dry-brush stroke, 0.3-1.3 s power1.out
   *  'box'      v5: opaque box, fixed 0.4 s linear; feather (px) = soft leading edge
   */
  highlight(sel, opts = {}) {
    const P = {
      pill:     { kind: 'block', pad: [0.02, 0.12, 0.0, 0.12], rot: -1.5, dur: 0.13, ease: 'power2.out', gap: 0.03, behind: true },
      low:      { kind: 'block', pad: [-0.40, 0.08, 0.18, 0.08], rot: 0, dur: 0.35, ease: 'power2.out', gap: 0.05, behind: true, radius: 0, alpha: 1 },
      marker:   { kind: 'marker', pad: [-0.32, 0.45, 0.10, 0.18], rot: 'rand', dur: 0.7, ease: 'none', gap: 0.27, behind: true },
      multiply: { kind: 'block', pad: [-0.10, 0.10, -0.02, 0.10], rot: 0, dur: 1.1, ease: 'sine.out', gap: 0.05, behind: false, blend: 'multiply', radius: 0, alpha: 1 },
      headline: { kind: 'torn', pad: [-0.02, 0.33, 0.10, 0.13], rot: 0, dur: 1.47, ease: EASE.hlBurst, gap: -0.6, behind: true, alpha: 1, blend: 'multiply', rough: 0.05 },
      torn:     { kind: 'torn', pad: [0.15, 0.20, 0.15, 0.14], rot: 0.6, dur: 0.92, ease: 'sine.out', gap: 0.05, behind: true, alpha: 1 },
      brush:    { kind: 'brush', pad: [0.05, 0.14, 0.18, 0.14], rot: -2, dur: 0.6, ease: 'power1.out', gap: 0.05, behind: true, alpha: 1 },
      box:      { kind: 'block', pad: [0.06, 0.20, 0.10, 0.30], rot: 0.5, dur: 0.4, ease: 'none', gap: 0.05, behind: true, alpha: 1, radius: 0, feather: 0 },
    };
    const o = { ...P[opts.preset || 'pill'], ...opts };
    const color = o.color || this.pal.yellow;
    const el = $(sel), tl = gsap.timeline(), r = rng(this.seed + (el.textContent.length * 13));
    el.classList.add('hl-text');
    const host = el.offsetParent || el.parentElement;
    const hostR = host.getBoundingClientRect(), k = hostR.width / host.offsetWidth || 1;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    let t = 0;
    const rects = [...el.getClientRects()].filter(rc => rc.width > 2);
    rects.forEach((rc, i) => {
      const m = document.createElement('div'); m.className = 'hl-mark';
      const [pt, pr, pb, pl] = o.pad.map(v => v * fs);
      const x = (rc.left - hostR.left) / k - pl + host.scrollLeft, y = (rc.top - hostR.top) / k - pt + host.scrollTop;
      const w = rc.width / k + pl + pr, h = rc.height / k + pt + pb;
      const rot = o.rot === 'rand' ? (r() - 0.6) * 2.4 : o.rot;
      Object.assign(m.style, {
        left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px', transform: `rotate(${rot}deg)`,
        backgroundImage: textures.marker({ kind: o.kind, color, seed: this.seed + i * 7 + 1, w: Math.round(w), h: Math.round(h), alpha: o.alpha ?? 0.92, radius: o.radius ?? 8 }),
        mixBlendMode: o.blend || 'normal', zIndex: o.behind ? 0 : 3,
      });
      host.appendChild(m);   // z-index orders it: behind = 0 (text gets 1), over = 3
      if (o.feather) {
        const fe = o.feather * this.u;
        m.style.webkitMaskImage = m.style.maskImage = `linear-gradient(90deg, #000 calc(var(--p) * 100%), transparent calc(var(--p) * 100% + ${fe}px))`;
        tl.fromTo(m, { '--p': -fe / w }, { '--p': 1, duration: o.dur, ease: o.ease, immediateRender: true }, t);
      } else tl.fromTo(m, { clipPath: 'inset(-30% 100% -30% 0)' }, { clipPath: 'inset(-30% 0% -30% 0)', duration: o.dur, ease: o.ease, immediateRender: true }, t);
      t += o.dur + o.gap;
    });
    return tl;
  }

  // ---------------------------------------------------------- paper pieces
  /** ragged clip-path for torn scraps / tags / bars. amp 5-10 px cards, 10-18 px page edges. sides ⊂ 'tblr' */
  torn(sel, { amp = 6, step = [10, 25], sides = 'tblr', seed } = {}) {
    $$(sel).forEach((el, k) => {
      const r = rng(seed ?? this.seed + 31 * (k + 1)), w = el.offsetWidth, h = el.offsetHeight, pts = [];
      const A = amp * this.u, st = () => (step[0] + r() * (step[1] - step[0])) * this.u;
      const j = s => (sides.includes(s) ? r() * A : 0);
      for (let x = 0; x < w; x += st()) pts.push([x, j('t')]);
      for (let y = 0; y < h; y += st()) pts.push([w - j('r'), y]);
      for (let x = w; x > 0; x -= st()) pts.push([x, h - j('b')]);
      for (let y = h; y > 0; y -= st()) pts.push([j('l'), y]);
      el.style.clipPath = `polygon(${pts.map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(',')})`;
    });
  }
  /**
   * Cut-out treatments for transparent PNG/SVG (filter stacks):
   *  'news'    v1: B&W high-contrast + solid crimson copy offset (+8,-3) px behind (reads as a hand-cut outline)
   *  'sticker' v2: white 6-10 px border + soft contact shadow (colour photo/illustration)
   *  'outline' v3: thick yellow 16 px outline, no shadow, B&W
   *  'offset'  v3: B&W + solid red duplicate offset (12,10) px, no blur
   *  'bw'      plain B&W high contrast
   */
  cutout(sel, { style = 'sticker', stroke, width, inner = '#ffffff', innerWidth, shadow = 'rgba(0,0,0,.26)', offset = [12, 10], bw } = {}) {
    const u = this.u, ring = (c, w) => Array.from({ length: 16 }, (_, i) => { const a = (i / 16) * Math.PI * 2; return `drop-shadow(${(Math.cos(a) * w).toFixed(2)}px ${(Math.sin(a) * w).toFixed(2)}px 0 ${c})`; }).join(' ');
    const BW = 'grayscale(1) contrast(1.2) brightness(1.03)';
    const f = {
      news: () => ['grayscale(1) contrast(1.35) brightness(1.02)', `drop-shadow(${(offset === undefined ? 8 : 8) * u}px ${-3 * u}px 0 ${stroke || this.pal.outline || this.pal.red})`, `drop-shadow(${3 * u}px ${-1 * u}px 0 ${stroke || this.pal.outline || this.pal.red})`],
      sticker: () => [bw ? BW : '', ring(inner, (innerWidth ?? 8) * u), `drop-shadow(0 ${6 * u}px ${10 * u}px ${shadow})`],
      outline: () => [bw === false ? '' : BW, ring(stroke || this.pal.yellow, (width ?? 16) * u)],
      offset: () => [BW, `drop-shadow(${offset[0] * u}px ${offset[1] * u}px 0 ${stroke || this.pal.red})`],
      bw: () => [BW],
    }[style]();
    $$(sel).forEach(el => { el.classList.add('cutout'); el.style.filter = f.filter(Boolean).join(' '); });
  }

  // ---------------------------------------------------------- motion atoms (content clock)
  /** generic pop: icons, pins, badges. back.out(1.7) slight overshoot; v2 #1 badge uses back.out(3) */
  pop(sel, { dur = 0.17, from = 0, ease = 'back.out(1.7)', stagger = 0, origin = '50% 50%', rot = 0 } = {}) {
    return gsap.timeline().fromTo($$(sel), { scale: from, rotation: rot, opacity: from ? 0 : 1 }, { scale: 1, rotation: 0, opacity: 1, duration: dur, ease, stagger, transformOrigin: origin, immediateRender: true });
  }
  /** v2 stamp/tag slam, squash profile: 1.8 -> 1.49 (opaque) -> 0.75 -> 1.0 over 0.35 s, constant rotation */
  slam(sel, { rot = -6, from = 1.8 } = {}) {
    return gsap.timeline().fromTo($$(sel), { scale: from, opacity: 0, rotation: rot }, {
      keyframes: [{ scale: 1.49, opacity: 1, duration: 0.05, ease: 'none' }, { scale: 0.75, duration: 0.13, ease: 'power2.in' }, { scale: 1, duration: 0.17, ease: 'power2.out' }], immediateRender: true,
    });
  }
  /** v2 cut-out tilt-in: opacity .3->1, scale 1.12->1, rot -8->0, y -10, 0.13 s back.out(1.4) */
  tiltIn(sel, { rot = -8, scale = 1.12, dur = 0.133 } = {}) {
    return gsap.timeline().fromTo($$(sel), { opacity: 0.3, scale, rotation: rot, y: -10 * this.u }, { opacity: 1, scale: 1, rotation: 0, y: 0, duration: dur, ease: 'back.out(1.4)', immediateRender: true });
  }
  /** v2 hourglass: tilt-rise from below: rot +14 -> 0, y +90 -> 0, 0.33 s power3.out */
  tiltRise(sel, { rot = 14, y = 90, dur = 0.33 } = {}) {
    return gsap.timeline().fromTo($$(sel), { opacity: 0, rotation: rot, y: y * this.u }, { keyframes: [{ opacity: 1, duration: 0.1, ease: 'none' }], rotation: 0, y: 0, duration: dur, ease: 'power3.out', immediateRender: true });
  }
  /** rise from below the frame (v1 photo, v3 hand/men 0.95-1.3 s power2.out, v2 receipt 0.33 s power3.out) */
  rise(sel, { dist = 600, dur = 0.8, ease = 'power2.out', from = 'bottom' } = {}) {
    const v = { bottom: { y: dist }, top: { y: -dist }, left: { x: -dist }, right: { x: dist } }[from];
    for (const q in v) v[q] *= this.u;
    return gsap.timeline().from($$(sel), { ...v, duration: dur, ease, immediateRender: true });
  }
  /** slide in from a screen edge (v3: 0.5-0.65 s power3.out/expo.out; linear 'conveyor' variant ease:'none') */
  slideIn(sel, { from = 'right', dist = 700, dur = 0.6, ease = 'power3.out', fade = false } = {}) {
    const v = { left: { x: -dist }, right: { x: dist }, top: { y: -dist }, bottom: { y: dist } }[from];
    for (const q in v) v[q] *= this.u;
    return gsap.timeline().from($$(sel), { ...v, opacity: fade ? 0 : 1, duration: dur, ease, immediateRender: true });
  }
  /** slide out (v3 title up & off: 0.4 s power2.in) */
  slideOut(sel, { to = 'top', dist = 500, dur = 0.4, ease = 'power2.in' } = {}) {
    const v = { left: { x: -dist }, right: { x: dist }, top: { y: -dist }, bottom: { y: dist } }[to];
    for (const q in v) v[q] *= this.u;
    return gsap.timeline().to($$(sel), { ...v, duration: dur, ease });
  }
  /** bars & growth from a base. v2 vertical bars back.out(1.1) 0.5 s (+4 % overshoot); horizontal power2.out 0.45 s, 0.05 s stagger */
  grow(sel, { dur = 0.5, axis = 'y', ease = axis === 'y' ? 'back.out(1.1)' : 'power2.out', origin = axis === 'x' ? '0% 50%' : '50% 100%', stagger = 0 } = {}) {
    const from = axis === 'y' ? { scaleY: 0 } : axis === 'x' ? { scaleX: 0 } : { scale: 0.03 };
    return gsap.timeline().fromTo($$(sel), from, { scaleY: 1, scaleX: 1, scale: 1, transformOrigin: origin, duration: dur, ease, stagger, immediateRender: true });
  }
  /** horizontal bar wipe via clip (keeps torn edges unstretched) */
  barWipe(sel, { dur = 0.45, ease = 'power2.out', stagger = 0.05 } = {}) {
    return gsap.timeline().fromTo($$(sel), { clipPath: 'inset(-20% 100% -20% 0)' }, { clipPath: 'inset(-20% 0% -20% 0)', duration: dur, ease, stagger, immediateRender: true });
  }
  /** v3 circle grow from a point: scale 0.03 -> 1, 1.1 s circ.out */
  growPoint(sel, { dur = 1.1, ease = 'circ.out' } = {}) {
    return gsap.timeline().fromTo($$(sel), { scale: 0.03 }, { scale: 1, duration: dur, ease, transformOrigin: '50% 50%', immediateRender: true });
  }
  /** rack-focus blur-out to swap content within a page (v2: blur 12, fade, 0.15 s power1.in) */
  blurOut(sel, { blur = 12, dur = 0.15, fade = true } = {}) { return gsap.timeline().to($$(sel), { filter: `blur(${blur}px)`, opacity: fade ? 0 : 1, duration: dur, ease: 'power1.in' }); }
  /** rack-focus in: from soft to sharp (v1) */
  focusIn(sel, { blur = 16, dur = 0.5, ease = 'power2.out' } = {}) { return gsap.timeline().fromTo($$(sel), { filter: `blur(${blur}px)` }, { filter: 'blur(0px)', duration: dur, ease, immediateRender: true }); }
  fadeOut(sel, { dur = 0.3, ease = 'none' } = {}) { return gsap.timeline().to($$(sel), { opacity: 0, duration: dur, ease }); }
  /** v2 "dim to the past": opacity -> 0.37, 0.25 s power2.inOut */
  dim(sel, { to = 0.37, dur = 0.25 } = {}) { return gsap.timeline().to($$(sel), { opacity: to, duration: dur, ease: 'power2.inOut' }); }
  /** FLIP rank reorder / move (v2: 0.43 s power2.inOut with lift scale 1.03) */
  moveBy(sel, { x = 0, y = 0, dur = 0.43, ease = 'power2.inOut', lift = 0 } = {}) {
    const tl = gsap.timeline().to($$(sel), { x: `+=${x * this.u}`, y: `+=${y * this.u}`, duration: dur, ease }, 0);
    if (lift) tl.to($$(sel), { scale: 1 + lift, duration: dur / 2, yoyo: true, repeat: 1, ease: 'sine.inOut' }, 0);
    return tl;
  }
  /** FLIP-move an element onto the box of `target` (v2 counter -> HUD card 0.2 s; year card -> corner 0.37 s) */
  flyTo(sel, target, { dur = 0.37, ease = 'power2.inOut' } = {}) {
    const el = $(sel), tg = $(target), k = this.stage.getBoundingClientRect().width / this.width;
    const a = el.getBoundingClientRect(), b = tg.getBoundingClientRect();
    return gsap.timeline().to(el, { x: ((b.left + b.width / 2) - (a.left + a.width / 2)) / k, y: ((b.top + b.height / 2) - (a.top + a.height / 2)) / k, scale: b.height / a.height, duration: dur, ease });
  }
  /** eased count-up for a stat (v2: power3.out ~0.6 s) */
  counter(sel, { from = 0, to = 100, dur = 0.6, ease = 'power3.out', prefix = '', suffix = '', decimals = 0 } = {}) {
    const el = $(sel), o = { v: from }, fmt = v => prefix + v.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix;
    el.textContent = fmt(from);
    return gsap.timeline().to(o, { v: to, duration: dur, ease, onUpdate: () => (el.textContent = fmt(o.v)) });
  }
  /** split-flap / ticking year card (v2: 2037->2048, 0.06 s per value, squashed half-glyph on each flip) */
  flipCount(sel, { from = 2037, to = 2048, each = 0.06 } = {}) {
    const el = $(sel), tl = gsap.timeline();
    for (let v = from, i = 0; v <= to; v++, i++) { tl.call(() => (el.textContent = v), null, i * each); tl.fromTo(el, { scaleY: 0.85 }, { scaleY: 1, duration: each * 0.6, ease: 'none' }, i * each); }
    tl.call(() => (el.textContent = to), null, (to - from + 1) * each);
    return tl;
  }
  /** live linear ticker (v2 "BORROWED SINCE YOU HIT PLAY" $77,105/s, quantised to 30 fps). Put on c.ctl. */
  ticker(sel, { rate = 77105, dur = 60, prefix = '$', suffix = '', q = 30, freezeAt, start = 0 } = {}) {
    const els = $$(sel), o = { t: 0 };
    const upd = () => { const tt = start + (freezeAt != null ? Math.min(o.t, freezeAt) : o.t); els.forEach(el => (el.textContent = prefix + Math.floor(Math.floor(tt * q) / q * rate).toLocaleString('en-US') + suffix)); };
    upd();
    return gsap.timeline().to(o, { t: dur, duration: dur, ease: 'none', onUpdate: upd });
  }
  /** icon grid pop: order 'random' (v3, 60 icons in ~0.9 s) or 'center' radial wave (v2, 0.27 s front) */
  gridPop(sel, { cols, order = 'random', amount = 0.8, dur = 0.13, ease = 'power2.out', origin = '50% 100%' } = {}) {
    const items = $$(sel), st = order === 'random' ? { amount, from: 'random' } : { amount, from: order, grid: cols ? [Math.ceil(items.length / cols), cols] : 'auto' };
    return gsap.timeline().fromTo(items, { scale: 0 }, { scale: 1, duration: dur, ease, transformOrigin: origin, stagger: st, immediateRender: true });
  }
  /** v3 horizontal-slice glitch reveal of a cut-out (clones into bands that snap in with steps(6)) */
  glitchIn(sel, { bands = 10, dur = 0.25, spread = 140, seed } = {}) {
    const el = $(sel), r = rng(seed ?? this.seed + 77), tl = gsap.timeline();
    const wrap = document.createElement('div'), cs = getComputedStyle(el);
    Object.assign(wrap.style, { position: 'absolute', left: el.offsetLeft + 'px', top: el.offsetTop + 'px', width: el.offsetWidth + 'px', height: el.offsetHeight + 'px' });
    el.parentNode.insertBefore(wrap, el);
    for (let i = 0; i < bands; i++) {
      const c = el.cloneNode(true); c.removeAttribute('id');
      Object.assign(c.style, { position: 'absolute', left: 0, top: 0, right: 'auto', bottom: 'auto', margin: 0, width: cs.width, height: cs.height, clipPath: `inset(${(i * 100) / bands}% 0 ${100 - ((i + 1) * 100) / bands}% 0)` });
      wrap.appendChild(c);
      tl.fromTo(c, { x: (r() - 0.5) * 2 * spread * this.u, scaleX: 1 + r() * 0.25, opacity: 0 }, { x: 0, scaleX: 1, opacity: 1, duration: dur, ease: 'steps(6)', immediateRender: true }, r() * dur * 0.8);
    }
    el.style.visibility = 'hidden';
    return tl;
  }
  /** stop-motion state swap (v3 jar fills: hard swaps every 0.25 s, no tween). els = ordered list of states */
  swap(sel, { each = 0.25 } = {}) {
    const els = $$(sel), tl = gsap.timeline();
    gsap.set(els, { visibility: 'hidden' });
    els.forEach((e, i) => { tl.set(e, { visibility: 'visible' }, i * each); if (i) tl.set(els[i - 1], { visibility: 'hidden' }, i * each); });
    return tl;
  }

  // ---------------------------------------------------------- hand-drawn strokes (SVG, world coords)
  svg(parent) {
    const s = document.createElementNS(svgNS, 'svg'); s.classList.add('draw');
    s.setAttribute('viewBox', `0 0 ${this.width} ${this.height}`); Object.assign(s.style, { left: 0, top: 0, width: this.width + 'px', height: this.height + 'px' });
    $(parent || this.world).appendChild(s); return s;
  }
  path(svg, d, { color = this.pal.red, width = 5, dash, cap = 'round', opacity = 1 } = {}) {
    const p = document.createElementNS(svgNS, 'path'); p.setAttribute('d', d);
    Object.entries({ stroke: color, 'stroke-width': width * this.u, 'stroke-linecap': cap, 'stroke-linejoin': 'round', fill: 'none', opacity }).forEach(([k, v]) => p.setAttribute(k, v));
    if (dash) p.dataset.dash = dash;
    svg.appendChild(p); return p;
  }
  /** draw-on via dashoffset. Dashed/dotted strokes (data-dash="22 12" or "0 21") keep their pattern via a mask. */
  drawOn(paths, { dur = 0.35, ease = 'power1.inOut', stagger = 0 } = {}) {
    const tl = gsap.timeline();
    $$(paths).forEach((p, i) => {
      let target = p;
      if (p.dataset.dash) {
        const svg = p.ownerSVGElement, id = 'mk' + Math.floor(rng(this.seed + i + svg.childNodes.length)() * 1e9);
        const mask = document.createElementNS(svgNS, 'mask'); mask.setAttribute('id', id); mask.setAttribute('maskUnits', 'userSpaceOnUse'); Object.entries({ x: -6000, y: -6000, width: 20000, height: 20000 }).forEach(([k, v]) => mask.setAttribute(k, v));
        const mp = p.cloneNode(); mp.removeAttribute('data-dash'); mp.setAttribute('stroke', '#fff'); mp.setAttribute('stroke-width', (+p.getAttribute('stroke-width')) * 3); mp.setAttribute('opacity', 1);
        mask.appendChild(mp); svg.appendChild(mask);
        p.setAttribute('stroke-dasharray', p.dataset.dash); p.setAttribute('mask', `url(#${id})`); target = mp;
      }
      const L = target.getTotalLength() + 2;
      target.style.strokeDasharray = `${L} ${L}`;
      gsap.set(p, { visibility: 'hidden' });   // round caps would otherwise show a dot before the draw starts
      tl.set(p, { visibility: 'visible' }, i * stagger);
      tl.fromTo(target, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: dur, ease, immediateRender: true }, i * stagger);
    });
    return tl;
  }
  /** erase tail-first (v3 write-off: 0.25 s power2.in) */
  drawOff(paths, { dur = 0.25, ease = 'power2.in' } = {}) { return gsap.timeline().to($$(paths), { strokeDashoffset: (i, p) => -(p.getTotalLength() + 2), duration: dur, ease }); }
  /** v3 "comet": head draws a loop while the tail erases behind it; nothing remains. 0.46 s power1.inOut */
  comet(paths, { dur = 0.46, ease = 'power1.inOut' } = {}) {
    const tl = gsap.timeline();
    $$(paths).forEach(p => { const L = p.getTotalLength() + 2; p.style.strokeDasharray = `${L} ${L}`; gsap.set(p, { visibility: 'hidden' }); tl.set(p, { visibility: 'visible' }, 0).fromTo(p, { strokeDashoffset: L }, { strokeDashoffset: -L, duration: dur, ease, immediateRender: true }, 0).set(p, { visibility: 'hidden' }, dur); });
    return tl;
  }
  /** hand-drawn ellipse path around box {x,y,w,h}: 1.1 loops open (v2/v3) or 1.85 loops (v5) */
  ellipsePath({ x, y, w, h }, { loops = 1.12, pad = 0.12, tilt = -2, ccw = false, seed } = {}) {
    const r = rng(seed ?? this.seed + Math.round(x + y)), cx = x + w / 2, cy = y + h / 2, rx = w / 2 + Math.max(w * pad, 14 * this.u), ry = h / 2 + Math.max(h * pad * 1.6, 12 * this.u);
    const N = Math.round(100 * loops), a0 = -Math.PI / 2 - 0.35, tr = tilt * Math.PI / 180, ph = r() * 6; let d = '';
    for (let i = 0; i <= N; i++) {
      const t = i / N, a = a0 + (ccw ? -1 : 1) * t * loops * Math.PI * 2;
      const g = 1 + 0.03 * Math.sin(t * 7 + ph) + 0.05 * t;   // drifting radius: loops never concentric
      const ex = rx * g * Math.cos(a), ey = ry * (1 + 0.07 * t) * Math.sin(a);
      d += `${i ? 'L' : 'M'}${(cx + ex * Math.cos(tr) - ey * Math.sin(tr)).toFixed(1)} ${(cy + ex * Math.sin(tr) + ey * Math.cos(tr)).toFixed(1)}`;
    }
    return d;
  }
  /**
   * element box relative to `ref` (default: the world). Both rects move with any transform on ref, so this is
   * safe to call while a scene/sheet is offset by its entry wipe. Measure BEFORE adding scale/slam tweens to `sel`.
   */
  box(sel, pad = 0, ref = this.world) {
    ref = $(ref);
    const el = $(sel), wr = ref.getBoundingClientRect(), k = wr.width / ref.offsetWidth || 1;
    let b = el.getBoundingClientRect();
    const ws = el._chars ? [...el.querySelectorAll('.w')] : [];
    if (ws.length) {   // split text: union of word wrappers (glyphs inside may be offset by a rise/pop tween)
      const rs = ws.map(w => w.getBoundingClientRect()), l = Math.min(...rs.map(r => r.left)), t = Math.min(...rs.map(r => r.top));
      b = { left: l, top: t, width: Math.max(...rs.map(r => r.right)) - l, height: Math.max(...rs.map(r => r.bottom)) - t };
      if (el.classList.contains('rise-mask')) { const fs = parseFloat(getComputedStyle(el).fontSize); b.top += fs * 0.22; b.height -= fs * 0.30; }
    } else if (el.textContent.trim() && !el.querySelector('img,svg')) { const r = document.createRange(); r.selectNodeContents(el); const rb = r.getBoundingClientRect(); if (rb.width) b = rb; }  // tight text box, not the block
    return { x: (b.left - wr.left) / k - pad, y: (b.top - wr.top) / k - pad, w: b.width / k + pad * 2, h: b.height / k + pad * 2 };
  }
  /** circle an element with a marker ellipse (v2 0.2 s, v3 persistent 0.15-0.21 s power2.out, v5 0.45 s 1.85 loops) */
  circle(sel, { svg, color = this.pal.red, width = 4.5, dur = 0.25, loops = 1.12, ccw = false, pad = 0.12, ease = 'power1.inOut', box } = {}) {
    svg = svg || this.svg();
    const p = this.path(svg, this.ellipsePath(box || this.box(sel, 0, svg.parentNode), { loops, ccw, pad }), { color, width });
    return { tl: this.drawOn(p, { dur, ease }), path: p };
  }
  /** curved hand-drawn arrow [x1,y1] -> [x2,y2]; head 'v' (two strokes) or 'loop' (v5 scribbled triangle) */
  arrow(from, to, { svg, color = this.pal.red, width = 4.5, bend = 0.22, head = 24, headStyle = 'v', dur = 0.33, ease = 'power2.inOut' } = {}) {
    svg = svg || this.svg();
    const [ax, ay] = from, [bx, by] = to, mx = (ax + bx) / 2 - (by - ay) * bend, my = (ay + by) / 2 + (bx - ax) * bend;
    const ang = Math.atan2(by - my, bx - mx), H = head * this.u, hA = 0.5;
    const body = this.path(svg, `M${ax} ${ay} Q${mx} ${my} ${bx} ${by}`, { color, width });
    const p1 = [bx - Math.cos(ang - hA) * H, by - Math.sin(ang - hA) * H], p2 = [bx - Math.cos(ang + hA) * H, by - Math.sin(ang + hA) * H];
    const hd = headStyle === 'loop' ? `M${bx} ${by} L${p1[0]} ${p1[1]} L${p2[0]} ${p2[1]} L${bx + Math.cos(ang) * 4} ${by + Math.sin(ang) * 4} L${(p1[0] + bx) / 2} ${(p1[1] + by) / 2}` : `M${p1[0]} ${p1[1]} L${bx} ${by} L${p2[0]} ${p2[1]}`;
    const hp = this.path(svg, hd, { color, width });
    const tl = gsap.timeline().add(this.drawOn(body, { dur, ease }), 0).add(this.drawOn(hp, { dur: headStyle === 'loop' ? 0.12 : 0.067, ease: 'none' }), dur * 0.9);
    return { tl, paths: [body, hp] };
  }
  /** underline (y≈1.0) or strike-through (y≈0.55) drawn L->R. v2: underline 0.25 s power2.inOut, strike 0.16 s power3.out */
  underline(sel, { svg, color = this.pal.red, width = 8, y = 1.0, dur = 0.25, over = 0.02, wobble = 3, ease = 'power2.inOut' } = {}) {
    svg = svg || this.svg();
    const b = this.box(sel, 0, svg.parentNode), yy = b.y + b.h * y, x0 = b.x - b.w * over, x1 = b.x + b.w * (1 + over);
    const p = this.path(svg, `M${x0} ${yy + wobble} Q${(x0 + x1) / 2} ${yy - wobble} ${x1} ${yy + wobble * 0.4}`, { color, width });
    return { tl: this.drawOn(p, { dur, ease }), path: p };
  }
  /** curly bracket under (or over) a box (v3: 0.3 s power1.out) */
  bracket(box, { svg, color = this.pal.red, width = 4, depth = 26, dur = 0.3 } = {}) {
    svg = svg || this.svg();
    const { x, y, w } = box, d = depth * this.u, m = x + w / 2;
    const p = this.path(svg, `M${x} ${y} Q${x} ${y + d / 2} ${x + d} ${y + d / 2} L${m - d} ${y + d / 2} Q${m} ${y + d / 2} ${m} ${y + d} Q${m} ${y + d / 2} ${m + d} ${y + d / 2} L${x + w - d} ${y + d / 2} Q${x + w} ${y + d / 2} ${x + w} ${y}`, { color, width });
    return { tl: this.drawOn(p, { dur, ease: 'power1.out' }), path: p };
  }
  /** connector line between two points; style 'solid' | 'dashed' | 'dotted' (v3) */
  connector(a, b, { svg, style = 'dotted', color = this.pal.red, width = 5, bend = 0.15, dur = 0.5, ease = 'power1.out' } = {}) {
    svg = svg || this.svg();
    const [ax, ay] = a, [bx, by] = b, mx = (ax + bx) / 2 - (by - ay) * bend, my = (ay + by) / 2 + (bx - ax) * bend;
    const dash = style === 'dotted' ? `0 ${width * 2.2 * this.u}` : style === 'dashed' ? `${22 * this.u} ${12 * this.u}` : null;
    const p = this.path(svg, `M${ax} ${ay} Q${mx} ${my} ${bx} ${by}`, { color, width, dash });
    return { tl: this.drawOn(p, { dur, ease }), path: p };
  }

  // ---------------------------------------------------------- camera (camera clock)
  /**
   * Rigid camera move of the whole desk (v3: tilt/pan/zoom 0.5-1.1 s expo.out or power2.inOut).
   * Absolute: scale s, looking at world point [ax, ay] (centre of frame). Use for push-ins and pull-outs.
   */
  camera({ scale = 1, look = [this.width / 2, this.height / 2], dur = 0.8, ease = 'power2.inOut', rotation } = {}) {
    const [ax, ay] = look, to = { scale, x: (this.width / 2 - ax) * scale, y: (this.height / 2 - ay) * scale, duration: dur, ease, transformOrigin: '50% 50%' };
    to.x = this.width / 2 - ax - (ax - this.width / 2) * (scale - 1); to.y = this.height / 2 - ay - (ay - this.height / 2) * (scale - 1);
    if (rotation != null) to.rotation = rotation;
    return gsap.timeline().to(this.cam, to);
  }
  /** relative pan/tilt (content moves by x,y px). Tilt-down to the next area = y: -1080 */
  move({ x = 0, y = 0, scale, dur = 0.65, ease = 'power2.inOut' } = {}) {
    const to = { x: `+=${x * this.u}`, y: `+=${y * this.u}`, duration: dur, ease };
    if (scale != null) to.scale = scale;
    return gsap.timeline().to(this.cam, to);
  }
  /** continuous push-in (v4 10-18 %/s; v1 slow; v2 CO2 chart 1.4 %/s). amount = scale gained over dur */
  push({ amount = 0.05, dur = 4, ease = 'none', target, from = 1 } = {}) {
    return gsap.timeline().fromTo(target ? $$(target) : this.cam, { scale: from }, { scale: from + amount, duration: dur, ease, transformOrigin: '50% 50%' });
  }
  /** slow hand-held roll (v5: ±2.2°, ~7 s cycle, sine.inOut with plateaus, slight 3D tilt) */
  roll({ amp = 2.2, period = 7, dur = 10, tilt3d = 1.2 } = {}) {
    const tl = gsap.timeline(), half = period / 2;
    gsap.set(this.cam, { transformPerspective: 2400 });
    tl.set(this.cam, { rotation: -0.2 }, 0);
    for (let t = 0, s = 1; t < dur; t += half, s = -s) tl.to(this.cam, { rotation: amp * s, rotationX: tilt3d * s, duration: half * 0.9, ease: 'sine.inOut' }, t);
    return tl;
  }
  /** v1 rack-focus pop on the whole frame: snap to `blur` px in 2 f, hold, release expo.out. Use with a push. */
  rackPop({ blur = 11, hold = 0.3, release = 0.16, pre = 1.7, preDur = 0.25 } = {}) {
    const el = this.cam;
    return gsap.timeline().fromTo(el, { filter: 'blur(0px)' }, { filter: `blur(${pre}px)`, duration: preDur, ease: 'power1.in', immediateRender: false })
      .to(el, { filter: `blur(${blur}px)`, duration: 0.033, ease: 'none' })
      .to(el, { filter: 'blur(0px)', duration: release, ease: 'expo.out' }, `+=${hold}`);
  }
  /** v1 slow hand-held drift: ±4 px wander at ~0.35 Hz (on the rig layer, so it never fights camera tweens) */
  drift({ amp = 4, dur = 10, fx = 0.4, fy = 0.33 } = {}) {
    const o = { t: 0 }, el = this.rig;
    return gsap.timeline().to(o, { t: dur, duration: dur, ease: 'none', onUpdate: () => gsap.set(el, { x: amp * Math.sin(o.t * 2 * Math.PI * fx), y: -amp * Math.sin(o.t * 2 * Math.PI * fy + 0.6) }) });
  }
  /** damped shake for heavy hits (not in the refs by default; keep amp small) */
  shake({ amp = 6, dur = 0.3, freq = 38 } = {}) {
    const o = { p: 0 }, r = rng(this.seed + 99), ph = [r() * 6, r() * 6], el = this.rig;
    return gsap.timeline().to(o, { p: 1, duration: dur, ease: 'none', onUpdate: () => { const k = (1 - o.p) ** 2, t = o.p * dur; gsap.set(el, { x: Math.sin(t * freq + ph[0]) * amp * k, y: Math.cos(t * freq * 1.3 + ph[1]) * amp * k }); } });
  }

  // ---------------------------------------------------------- transitions (camera clock)
  /**
   * Torn-paper sheet wipe (v2's ONLY scene change). `sheet` = a .sheet element (full-frame, own paper) holding
   * the next scene, placed inside the world. dir 'up' (from bottom, 0.22 s power2.out) | 'left' (from right, 0.2 s expo.out).
   * Old scene `old` blurs ~18 px within 0.08 s and freezes underneath, then is hidden.
   * paper: Comp.setPaper kind for the sheet (default: same as stage); black sheet: { base: '#050505' }.
   */
  pageWipe(sheet, { dir = 'up', dur = dir === 'up' ? 0.22 : 0.2, ease = dir === 'up' ? 'power2.out' : 'expo.out', old, paper = 'graph', paperOpts = {}, amp = 14, rim = '#f5f2ea' } = {}) {
    const el = $(sheet), W = this.width, H = this.height, u = this.u;
    if (!el._wipe) {
      el.classList.add('sheet');
      this.setPaper(paper, { gridGap: 45, ...paperOpts, target: el });
      const r = rng(this.seed + 404 + (el.id || 'x').charCodeAt(0)), A = amp * u, edge = [], rimEdge = [];
      // leading torn edge (sheet) + a wider, rougher fibre rim just ahead of it + a soft shadow strip
      const steps = []; for (let q = -40; q <= (dir === 'left' ? H : W) + 40; q += (15 + r() * 25) * u) steps.push([q, r() * A, (8 + r() * 14) * u]);
      let clip, rclip;
      if (dir === 'left') {
        clip = `polygon(${steps.map(([y, j]) => `${j.toFixed(1)}px ${y.toFixed(0)}px`).join(',')}, ${W + 60}px ${H + 40}px, ${W + 60}px -40px)`;
        rclip = `polygon(${steps.map(([y, j, k]) => `${(j - k).toFixed(1)}px ${y.toFixed(0)}px`).join(',')}, ${W + 60}px ${H + 40}px, ${W + 60}px -40px)`;
      } else {
        clip = `polygon(${steps.map(([x, j]) => `${x.toFixed(0)}px ${j.toFixed(1)}px`).reverse().join(',')}, -40px ${H + 60}px, ${W + 40}px ${H + 60}px)`;
        rclip = `polygon(${steps.map(([x, j, k]) => `${x.toFixed(0)}px ${(j - k).toFixed(1)}px`).reverse().join(',')}, -40px ${H + 60}px, ${W + 40}px ${H + 60}px)`;
      }
      el.style.clipPath = clip;
      const rimEl = document.createElement('div'); rimEl.className = 'sheet-rim'; Object.assign(rimEl.style, { background: rim, clipPath: rclip });
      const sh = document.createElement('div'); sh.className = 'sheet-shadow sheet-shadow-' + dir;
      el.parentNode.insertBefore(sh, el); el.parentNode.insertBefore(rimEl, el);
      el._wipe = [sh, rimEl, el];
    }
    const group = el._wipe, tl = gsap.timeline();
    tl.set(group, { visibility: 'visible' }, 0);
    if (old) tl.to($$(old), { filter: 'blur(18px) brightness(.96)', duration: 0.08, ease: 'power1.out' }, 0);
    tl.fromTo(group, dir === 'left' ? { x: W + 80 } : { y: H + 80 }, dir === 'left' ? { x: 0, duration: dur, ease } : { y: 0, duration: dur, ease }, 0);
    if (old) tl.set($$(old), { visibility: 'hidden' }, dur);
    tl.set(group.slice(0, 2), { visibility: 'hidden' }, dur + 0.05);
    return tl;
  }
  /** white light-leak blob sweeping across a cut (v4 cut 1: 8 frames @24 ≈ 0.33 s, screen blend) */
  lightLeak({ dur = 0.33, from = [75, -10], to = [20, 60], peak = 0.9 } = {}) {
    const d = this._div('fx-leak', this.fx);
    return gsap.timeline().fromTo(d, { opacity: 0, left: from[0] + '%', top: from[1] + '%' }, { keyframes: [{ opacity: peak * 0.6, duration: dur * 0.12 }, { opacity: peak, left: (from[0] + to[0]) / 2 + '%', top: (from[1] + to[1]) / 2 + '%', duration: dur * 0.5 }, { opacity: 0, left: to[0] + '%', top: to[1] + '%', duration: dur * 0.38 }], ease: 'sine.inOut', immediateRender: true });
  }
  /** exposure pulse (v4: attack 1-2 f, decay 2-3 f, +8..11 % luminance) */
  flash({ peak = 0.3, attack = 0.06, decay = 0.1, color = '#fff' } = {}) {
    const d = this._div('fx-flash', this.fx); d.style.background = color;
    return gsap.timeline().fromTo(d, { opacity: 0 }, { opacity: peak, duration: attack, ease: 'none', immediateRender: true }).to(d, { opacity: 0, duration: decay, ease: 'power1.out' });
  }
  /** decaying projector flicker (v4 S1: ±6 % at ~3 Hz, gone by 1.3 s) */
  flicker({ dur = 1.3, amp = 0.12, fps = 24 } = {}) {
    const d = this._div('fx-flash', this.fx), tl = gsap.timeline(), n = Math.round(dur * fps);
    Object.assign(d.style, { background: '#fff', mixBlendMode: 'soft-light' });
    for (let f = 0; f <= n; f++) tl.set(d, { opacity: f === n ? 0 : amp * (1 - f / n) * (0.5 + 0.5 * Math.sin(f * 0.83 + Math.sin(f * 2.1))) }, f / fps);
    return tl;
  }
  /** v3 light-leak + colour-tint flicker between "worlds" (1.0 s, stepped 12 fps). Put the hard cut at +0.5 s. */
  tintFlicker() {
    const tint = this._div('fx-flash', this.fx), leak = this._div('fx-leak', this.fx), tl = gsap.timeline();
    tint.style.mixBlendMode = 'color'; Object.assign(leak.style, { left: '55%', top: '5%', width: '70%', height: '90%' });
    [[0, '#6E5E9A', .8, 1, 0], [.13, '#3B4C7A', .85, 0, 0], [.33, '#30405A', .3, 0, 0], [.38, '#B060C0', .75, 0, 0], [.5, '#9A60C0', .8, 0, 0],
     [.59, '#F6B6DA', .9, .9, .7], [.76, '#E07AC0', .7, 0, .2], [.84, '#C07AA0', .5, 0, 0], [.93, '#8A6A90', .35, 0, 0], [1, '#000', 0, 0, 0]]
      .forEach(([dt, c, o, lo, ov]) => tl.set(tint, { backgroundColor: c, opacity: o }, dt).set(leak, { opacity: Math.max(lo, ov) }, dt));
    return tl;
  }
}

export { gsap };
