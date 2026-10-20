// Kad teks B-roll (tajuk hook, hadis/ayat Arab, CTA) — port dari broll/templates/card.html.
// Props sama dengan data kad dalam broll/reels/*.json:
//  kind      — 'title' | 'hadith' | 'cta'
//  lines     — baris teks (title/cta: condensed uppercase ditaip masuk; hadith: baris kecil bawah teks Arab)
//  highlight — teks yang jadi kuning #FFD400
//  arabic    — teks Arab (hadith), satu rentetan atau senarai baris
//  source    — kredit di bawah kad ("Sumber: ...")
//  duration  — saat (min 2, lalai 2.5)
//  full      — true = latar ungu gelap penuh; false = lutsinar untuk ditindih atas footage
//  instant   — true = teks penuh dari frame pertama (hook 0-1s)
import { AbsoluteFill, CalculateMetadataFunction, interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";
import { CSSProperties } from "react";
import "./fonts";

export type CardProps = {
  kind: "title" | "hadith" | "cta";
  lines?: string[];
  highlight?: string;
  arabic?: string | string[];
  source?: string;
  duration?: number;
  full?: boolean;
  instant?: boolean;
};

export const cardDuration = (p: CardProps) => Math.max(2, p.duration || 2.5);

export const calculateCardMetadata: CalculateMetadataFunction<CardProps> = ({ props }) => ({
  durationInFrames: Math.round(cardDuration(props) * 30),
});

const seg = (t: number, a: number, b: number) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const back = (t: number) => { const c = 1.6; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };

const BG: Record<CardProps["kind"], string> = {
  title: "radial-gradient(ellipse at 50% 40%, #251634 0%, #150F20 55%, #0a0710 100%)",
  hadith: "radial-gradient(ellipse at 50% 40%, #2b1a3e 0%, #150F20 55%, #0a0710 100%)",
  cta: "radial-gradient(ellipse at 50% 40%, #3a2356 0%, #1E122F 50%, #0a0710 100%)",
};

const GRAIN = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='.9'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`;

const card: CSSProperties = {
  position: "absolute", left: 150, top: 300, width: 780, height: 975, borderRadius: 28, overflow: "hidden",
  boxShadow: "0 30px 80px rgba(0,0,0,.65), inset 0 0 120px rgba(0,0,0,.7)", transformOrigin: "50% 50%",
  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center",
  boxSizing: "border-box", padding: 60,
};
const big: CSSProperties = {
  fontFamily: "'Bebas Neue', sans-serif", color: "#fff", fontSize: 150, lineHeight: 0.95,
  letterSpacing: "0.01em", textTransform: "uppercase",
};
const ar: CSSProperties = {
  fontFamily: "'Amiri', serif", fontWeight: 700, color: "#fff", fontSize: 88, lineHeight: 1.8, direction: "rtl",
  textShadow: "0 0 40px rgba(255,255,255,.3)",
};
const sub: CSSProperties = { color: "#9A9691", fontSize: 30, letterSpacing: "0.04em", marginTop: 10 };
const rule: CSSProperties = { height: 6, background: "#A5E09F", margin: "40px auto", borderRadius: 3 };

export const Card: React.FC<CardProps> = (p) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = cardDuration(p);
  const t0 = frame / fps;
  const t = t0 + (p.instant ? 1.2 : 0);
  const lines = p.lines || [];

  const pop = back(seg(t, 0, 0.45));
  // v2.0: gerakan halus sepanjang klip — zoom perlahan 100%→103% selepas kad masuk
  const drift = interpolate(t0, [0, dur], [1, 1.03]);
  const ruleW = seg(t, 0.5, 1.1) * 260;

  // aksara "ditaip masuk" ikut urutan semua baris
  const total = lines.reduce((n, l) => n + [...l].length, 0);
  const typeEnd = Math.min(0.85, dur * 0.4);
  let idx = 0;

  return (
    <AbsoluteFill style={{ opacity: 1 - seg(t0, dur - 0.25, dur), fontFamily: "Inter, sans-serif" }}>
      {p.full && (
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 42%, #251634 0%, #150F20 45%, #0a0710 80%)" }} />
      )}
      <div style={{ ...card, background: BG[p.kind], opacity: seg(t, 0, 0.2), transform: `scale(${(0.88 + 0.12 * pop) * drift})` }}>
        {p.kind === "hadith" ? (
          <>
            <div style={{ ...ar, opacity: seg(t, 0.25, 0.9) }}>
              {([] as string[]).concat(p.arabic || []).map((l, i) => <div key={i}>{l}</div>)}
            </div>
            <div style={{ ...rule, width: ruleW }} />
            {lines.map((l, i) => <div key={i} style={sub}>{l}</div>)}
          </>
        ) : (
          <>
            <div style={big}>
              {lines.map((l, li) => {
                const hi = p.highlight || "";
                const at = hi ? l.indexOf(hi) : -1;
                return (
                  <span key={li} style={{ display: "block" }}>
                    {[...l].map((ch, i) => {
                      const shown = t >= 0.2 + (idx++ / total) * (typeEnd - 0.2);
                      const yellow = at >= 0 && i >= at && i < at + hi.length;
                      return <span key={i} style={{ opacity: shown ? 1 : 0, color: yellow ? "#FFD400" : undefined }}>{ch}</span>;
                    })}
                  </span>
                );
              })}
            </div>
            <div style={{ ...rule, width: ruleW }} />
          </>
        )}
      </div>
      {p.source && (
        <div style={{ position: "absolute", left: 150, width: 780, top: 1290, textAlign: "center", color: "#9a9691",
                      fontSize: 22, letterSpacing: "0.02em", opacity: seg(t, 0.4, 0.8) }}>
          Sumber: {p.source}
        </div>
      )}
      {/* tekstur wajib: grain, berkelip setiap frame */}
      <AbsoluteFill style={{ opacity: 0.14, backgroundImage: GRAIN,
                             backgroundPosition: `${Math.floor(random(`gx${frame}`) * 160)}px ${Math.floor(random(`gy${frame}`) * 160)}px` }} />
    </AbsoluteFill>
  );
};
