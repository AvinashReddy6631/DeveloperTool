import { useEffect, useRef } from "react";

const NODE_DEFS = [
  { id: "salary", label: "Salary Agent", angle: -1.22, tint: "250, 250, 250" },
  { id: "company", label: "Company Agent", angle: -0.22, tint: "212, 212, 216" },
  { id: "weather", label: "Weather Agent", angle: 0.72, tint: "161, 161, 170" },
  { id: "general", label: "General Agent", angle: 2.12, tint: "228, 228, 231" },
  { id: "repo", label: "Repository Intelligence", angle: 3.42, tint: "244, 244, 245" },
];

function prefersReducedMotion() {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

function roundRect(ctx, x, y, w, h, r) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}

export default function IntelligenceNetwork() {
  const canvasRef = useRef(null);
  const stageRef = useRef(null);
  const routeRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const stage = stageRef.current;
    if (!canvas || !stage) return undefined;

    const ctx = canvas.getContext("2d", { alpha: true, desynchronized: true });
    if (!ctx) return undefined;

    const reduced = prefersReducedMotion();
    const pointer = { x: 0, y: 0 };
    const pointerTarget = { x: 0, y: 0 };

    let width = 0;
    let height = 0;
    let dpr = 1;
    let compact = false;
    let frame = 0;
    let running = false;
    let visible = false;
    let pageHidden = document.hidden;

    const packets = NODE_DEFS.flatMap((_, i) => [
      { edge: i, t: (i * 0.19) % 1, speed: 0.22 + (i % 3) * 0.05, reverse: false },
      { edge: i, t: (i * 0.37 + 0.45) % 1, speed: 0.14 + (i % 2) * 0.03, reverse: true },
    ]);

    const dust = Array.from({ length: 48 }, (_, i) => ({
      x: Math.random(),
      y: Math.random(),
      z: 0.35 + (i % 5) * 0.14,
      r: 0.5 + (i % 4) * 0.22,
      drift: 0.012 + (i % 6) * 0.003,
    }));

    let origin = 0;
    let routeIndex = 0;
    let routeUntil = 2.4;
    let flashT = 1;

    const resize = () => {
      const bounds = stage.getBoundingClientRect();
      const nextW = Math.max(1, Math.round(bounds.width));
      const nextH = Math.max(1, Math.round(bounds.height));
      const nextCompact = nextW < 760;
      const nextDpr = Math.min(
        window.devicePixelRatio || 1,
        nextW < 430 ? 1.1 : nextCompact ? 1.25 : 1.75
      );

      if (
        nextW === width &&
        nextH === height &&
        nextDpr === dpr &&
        nextCompact === compact
      ) {
        return;
      }

      width = nextW;
      height = nextH;
      dpr = nextDpr;
      compact = nextCompact;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const glow = (x, y, radius, color, alpha) => {
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      gradient.addColorStop(0, `rgba(${color}, ${alpha})`);
      gradient.addColorStop(1, `rgba(${color}, 0)`);
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fill();
    };

    const nodePoint = (def, time, radius, ox, oy) => {
      const orbit = reduced ? 0 : Math.sin(time * 0.62 + def.angle) * (compact ? 4 : 8);
      const spin = reduced ? 0 : time * 0.07;
      const a = def.angle + spin * 0.1;
      return {
        x: width * 0.5 + Math.cos(a) * (radius + orbit) + ox * 0.72,
        y: height * 0.52 + Math.sin(a) * (radius * 0.78 + orbit * 0.45) + oy * 0.72,
      };
    };

    const drawFrame = (stamp) => {
      if (!origin) origin = stamp || 1;
      const time = reduced ? 0 : (stamp - origin) / 1000;
      pointer.x += (pointerTarget.x - pointer.x) * 0.045;
      pointer.y += (pointerTarget.y - pointer.y) * 0.045;

      const ox = pointer.x * (compact ? 8 : 16);
      const oy = pointer.y * (compact ? 6 : 12);
      const radius = Math.min(width, height) * (compact ? 0.26 : 0.32);

      ctx.clearRect(0, 0, width, height);

      glow(
        width * 0.5 + ox * 1.2,
        height * 0.42 + oy,
        compact ? 140 : 240,
        "78, 42, 190",
        0.18
      );

      const dustCount = compact ? 14 : width < 1100 ? 26 : 48;
      for (let i = 0; i < dustCount; i += 1) {
        const speck = dust[i];
        const px =
          ((speck.x + (reduced ? 0 : time * speck.drift * 0.035)) % 1) * width;
        const py =
          ((speck.y + (reduced ? 0 : Math.sin(time * 0.18 + i) * 0.008)) % 1) *
          height;
        ctx.fillStyle = `rgba(255, 255, 255, ${0.04 + speck.z * 0.04})`;
        ctx.beginPath();
        ctx.arc(px, py, speck.r, 0, Math.PI * 2);
        ctx.fill();
      }

      const cx = width * 0.5 + ox * 0.28;
      const cy = height * 0.52 + oy * 0.24;
      const breath = reduced ? 1 : 1 + Math.sin(time * 1.55) * 0.045;

      ctx.save();
      ctx.translate(cx, cy);
      const rings = compact ? [radius * 0.78] : [radius * 0.52, radius * 0.78, radius * 1.06];
      rings.forEach((ring, i) => {
        ctx.strokeStyle = `rgba(255, 255, 255, ${0.12 - i * 0.02})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.ellipse(0, 0, ring * 1.04, ring * 0.7, i * 0.4, 0, Math.PI * 2);
        ctx.stroke();
      });
      ctx.restore();

      if (!reduced && time > routeUntil) {
        routeIndex = (routeIndex + 1) % NODE_DEFS.length;
        routeUntil = time + 2.6 + (routeIndex % 3) * 0.35;
        flashT = 0;
        if (routeRef.current) {
          routeRef.current.textContent = NODE_DEFS[routeIndex].label;
        }
      }

      if (!reduced && flashT < 1) {
        flashT = Math.min(1, flashT + 0.018);
      }

      const nodes = NODE_DEFS.map((def) => nodePoint(def, time, radius, ox, oy));

      nodes.forEach((point, i) => {
        const active = i === routeIndex;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(point.x, point.y);
        ctx.strokeStyle = active
          ? `rgba(250, 250, 250, ${0.5 + (1 - flashT) * 0.3})`
          : "rgba(255, 255, 255, 0.18)";
        ctx.lineWidth = active ? 1.6 : 1;
        ctx.stroke();
      });

      if (!reduced) {
        const packetLimit = compact ? 5 : packets.length;
        for (let i = 0; i < packetLimit; i += 1) {
          const packet = packets[i];
          packet.t += packet.speed * 0.0075;
          if (packet.t > 1) packet.t -= 1;
          const target = nodes[packet.edge];
          const t = packet.reverse ? 1 - packet.t : packet.t;
          const x = cx + (target.x - cx) * t;
          const y = cy + (target.y - cy) * t;
          const hot = packet.edge === routeIndex;
          ctx.fillStyle = hot ? "#fafafa" : "#a1a1aa";
          ctx.beginPath();
          ctx.arc(x, y, hot ? 2.2 : 1.4, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      nodes.forEach((point, i) => {
        const active = i === routeIndex;
        const r = (compact ? 6 : 9) * (reduced ? 1 : 1 + Math.sin(time * 2 + i) * 0.06);
        ctx.fillStyle = "rgba(9, 9, 11, 0.94)";
        ctx.beginPath();
        ctx.arc(point.x, point.y, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = active
          ? "rgba(250, 250, 250, 0.95)"
          : "rgba(161, 161, 170, 0.7)";
        ctx.lineWidth = 1.1;
        ctx.stroke();

        if (!compact) {
          const label = NODE_DEFS[i].label;
          ctx.font = "500 11px Geist Variable, Inter, sans-serif";
          const textW = ctx.measureText(label).width;
          const left = point.x >= cx;
          const lx = left ? point.x + 14 : point.x - 14 - textW - 14;
          ctx.fillStyle = "rgba(9, 9, 11, 0.72)";
          roundRect(ctx, lx, point.y - 11, textW + 14, 22, 3);
          ctx.fill();
          ctx.fillStyle = "rgba(250, 250, 250, 0.88)";
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";
          ctx.fillText(label, lx + 7, point.y);
        }
      });

      const core = (compact ? 28 : 36) * breath;
      glow(cx, cy, compact ? 48 : 78, "250, 250, 250", 0.16);
      ctx.fillStyle = "#09090b";
      ctx.beginPath();
      ctx.arc(cx, cy, core, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "rgba(250, 250, 250, 0.88)";
      ctx.lineWidth = 1.35;
      ctx.stroke();

      ctx.fillStyle = "#fafafa";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = compact
        ? "600 8px Geist Variable, Inter, sans-serif"
        : "600 11px Geist Variable, Inter, sans-serif";
      ctx.fillText("MCP", cx, cy - 6);
      ctx.fillStyle = "rgba(161, 161, 170, 0.95)";
      ctx.font = compact
        ? "500 7px Geist Variable, Inter, sans-serif"
        : "500 9px Geist Variable, Inter, sans-serif";
      ctx.fillText("ORCHESTRATOR", cx, cy + 7);
    };

    const tick = (stamp) => {
      if (!running) return;
      drawFrame(stamp);
      frame = window.requestAnimationFrame(tick);
    };

    const start = () => {
      if (reduced || running || !visible || pageHidden) return;
      running = true;
      frame = window.requestAnimationFrame(tick);
    };

    const stop = () => {
      running = false;
      window.cancelAnimationFrame(frame);
      frame = 0;
    };

    const onPointerMove = (event) => {
      if (reduced || compact) return;
      const bounds = stage.getBoundingClientRect();
      pointerTarget.x = Math.max(
        -1,
        Math.min(1, ((event.clientX - bounds.left) / bounds.width) * 2 - 1)
      ) * 0.5;
      pointerTarget.y = Math.max(
        -1,
        Math.min(1, ((event.clientY - bounds.top) / bounds.height) * 2 - 1)
      ) * 0.5;
    };

    const onPointerLeave = () => {
      pointerTarget.x = 0;
      pointerTarget.y = 0;
    };

    const resizeObserver = new ResizeObserver(() => {
      resize();
      if (reduced || !running) drawFrame(origin || 0);
    });

    const intersect = new IntersectionObserver(
      ([entry]) => {
        visible = Boolean(entry?.isIntersecting);
        if (visible) start();
        else stop();
      },
      { threshold: 0.08, rootMargin: "80px 0px" }
    );

    const onVisibility = () => {
      pageHidden = document.hidden;
      if (pageHidden) stop();
      else start();
    };

    resize();
    drawFrame(0);
    if (routeRef.current) {
      routeRef.current.textContent = NODE_DEFS[0].label;
    }

    stage.addEventListener("pointermove", onPointerMove, { passive: true });
    stage.addEventListener("pointerleave", onPointerLeave);
    resizeObserver.observe(stage);
    intersect.observe(stage);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      stop();
      stage.removeEventListener("pointermove", onPointerMove);
      stage.removeEventListener("pointerleave", onPointerLeave);
      document.removeEventListener("visibilitychange", onVisibility);
      resizeObserver.disconnect();
      intersect.disconnect();
    };
  }, []);

  return (
    <div className="di-network">
      <p className="di-sr-only">
        Animated Developer Intelligence network. A user request flows to the
        MCP Orchestrator, then to a specialized agent, through processing, and
        back as a response.
      </p>

      <div className="di-network-stage" ref={stageRef}>
        <svg className="di-network-frame" viewBox="0 0 100 100" aria-hidden="true">
          <path d="M8 22 V8 H22" />
          <path d="M92 22 V8 H78" />
          <path d="M8 78 V92 H22" />
          <path d="M92 78 V92 H78" />
        </svg>

        <ol className="di-network-flow" aria-hidden="true">
          <li>User request</li>
          <li>MCP Orchestrator</li>
          <li>Specialized agent</li>
          <li>Processing</li>
          <li>Response</li>
        </ol>

        <div className="di-network-live" aria-hidden="true">
          <span className="di-network-dot" aria-hidden="true" />
          <span>Routing</span>
          <strong ref={routeRef}>Salary Agent</strong>
        </div>

        <canvas ref={canvasRef} aria-hidden="true" />
      </div>

      <ul className="di-network-legend" aria-label="Connected agents">
        {NODE_DEFS.map((node) => (
          <li key={node.id}>{node.label}</li>
        ))}
      </ul>
    </div>
  );
}
