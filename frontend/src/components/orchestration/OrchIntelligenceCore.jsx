import { useEffect, useRef } from "react";
import { AGENT_CATALOG } from "../../lib/orchestrationAgents";
import { VIS_FLOW } from "../../lib/orchestrationScene";
import { useOrchVis } from "./OrchVisContext";

export default function OrchIntelligenceCore() {
  const canvasRef = useRef(null);
  const stageRef = useRef(null);
  const vis = useOrchVis();
  const visRef = useRef(vis);
  const kickRef = useRef(() => {});
  visRef.current = vis;

  useEffect(() => {
    const canvas = canvasRef.current;
    const stage = stageRef.current;
    if (!canvas || !stage) return undefined;

    const ctx = canvas.getContext("2d", { alpha: true, desynchronized: true });
    if (!ctx) return undefined;

    const reducedQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    let width = 0;
    let height = 0;
    let dpr = 1;
    let frame = 0;
    let running = false;
    let visible = false;
    let origin = 0;
    let lastPlay = "";
    let burst = 1;

    const packets = AGENT_CATALOG.map((_, i) => ({
      i,
      t: (i * 0.17) % 1,
      speed: 0.42 + (i % 3) * 0.08,
    }));

    const resize = () => {
      const bounds = stage.getBoundingClientRect();
      width = Math.max(1, Math.round(bounds.width));
      height = Math.max(1, Math.round(bounds.height));
      dpr = Math.min(
        window.devicePixelRatio || 1,
        width < 430 ? 1.1 : width < 760 ? 1.25 : 1.5
      );
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const glow = (x, y, r, color, a) => {
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, `rgba(${color}, ${a})`);
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    };

    const layout = () => {
      const cx = width * 0.5;
      const cy = height * 0.46;
      const radius = Math.min(width, height) * 0.34;
      const user = { x: cx, y: Math.min(height - 22, cy + radius * 0.92 + 28) };
      const nodes = AGENT_CATALOG.map((agent, i) => {
        const a = -Math.PI / 2 + (i / AGENT_CATALOG.length) * Math.PI * 2;
        return {
          ...agent,
          x: cx + Math.cos(a) * radius,
          y: cy + Math.sin(a) * radius * 0.78,
        };
      });
      return { cx, cy, user, nodes, radius };
    };

    const draw = (stamp, dt = 0.016) => {
      const visNow = visRef.current;
      const reduced = reducedQuery.matches || visNow.reduced;
      if (!origin) origin = stamp || 1;
      const time = reduced ? 0 : (stamp - origin) / 1000;
      if (visNow.play !== lastPlay) {
        lastPlay = visNow.play;
        burst = 0;
      }
      burst = Math.min(1, burst + dt * 2.8);

      ctx.clearRect(0, 0, width, height);
      const { cx, cy, user, nodes, radius } = layout();

      ctx.strokeStyle = "rgba(126,231,255,0.07)";
      ctx.lineWidth = 0.6;
      for (let i = 1; i <= 3; i += 1) {
        ctx.beginPath();
        ctx.ellipse(cx, cy, radius * (0.55 + i * 0.22), radius * (0.42 + i * 0.16), 0, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.lineWidth = 1;
      const play = visNow.play;
      const routed = visNow.agents;
      const error = play === "error";
      const thinking = play === "mcp";
      const selected = play === "selected";
      const processing = play === "processing";
      const returning = play === "returning";
      const complete = play === "complete";
      const hubHot = thinking || selected || processing || returning;
      const hubColor = error ? "180,40,60" : hubHot ? "40,210,255" : "80,40,200";

      glow(cx, cy, hubHot ? 150 : 110, hubColor, hubHot ? 0.28 : 0.14);

      ctx.beginPath();
      ctx.moveTo(user.x, user.y);
      ctx.lineTo(cx, cy);
      ctx.strokeStyle =
        visNow.queryReceived || thinking
          ? "rgba(126,231,255,0.55)"
          : "rgba(130,110,255,0.18)";
      ctx.lineWidth = visNow.queryReceived ? 1.6 : 1;
      ctx.stroke();
      ctx.lineWidth = 1;

      nodes.forEach((node) => {
        const known = routed.includes(node.id);
        const scanning = thinking;
        const lit = known && (selected || processing || returning || complete);
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(node.x, node.y);
        ctx.strokeStyle = lit
          ? `rgba(${node.tint},0.85)`
          : scanning
            ? "rgba(90,230,255,0.28)"
            : "rgba(130,110,255,0.16)";
        ctx.lineWidth = lit ? 1.8 : 1;
        ctx.stroke();
        ctx.lineWidth = 1;
      });

      if (!reduced) {
        if (thinking) {
          const t = (time * 0.85) % 1;
          ctx.fillStyle = "#e7fdff";
          ctx.beginPath();
          ctx.arc(
            user.x + (cx - user.x) * t,
            user.y + (cy - user.y) * t,
            2.4,
            0,
            Math.PI * 2
          );
          ctx.fill();
        }

        packets.forEach((packet) => {
          const node = nodes[packet.i];
          const known = routed.includes(node.id);
          let active = false;
          let reverse = false;

          if (thinking) {
            active = true;
            reverse = false;
          } else if (selected && known) {
            active = true;
            reverse = false;
          } else if ((processing || returning) && known) {
            active = true;
            reverse = true;
          }

          if (!active) return;

          packet.t = (packet.t + packet.speed * dt) % 1;
          const t = reverse ? 1 - packet.t : packet.t;
          const x = cx + (node.x - cx) * t;
          const y = cy + (node.y - cy) * t;
          ctx.fillStyle = known ? `rgb(${node.tint})` : "#d6f7ff";
          ctx.beginPath();
          ctx.arc(x, y, known ? 3.2 : 2.4, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = known ? `rgba(${node.tint},0.35)` : "rgba(214,247,255,0.28)";
          ctx.beginPath();
          ctx.arc(
            cx + (node.x - cx) * Math.max(0, t - 0.08),
            cy + (node.y - cy) * Math.max(0, t - 0.08),
            1.6,
            0,
            Math.PI * 2
          );
          ctx.fill();
        });
      }

      nodes.forEach((node) => {
        const known = routed.includes(node.id);
        const lit = known && (selected || processing || returning || complete);
        const scanning = thinking;
        const pulse =
          !reduced && processing && known
            ? 1 + Math.sin(time * 8) * 0.18
            : 1;

        if (lit) {
          glow(node.x, node.y, 26 * pulse, node.tint, 0.45);
        } else if (scanning) {
          glow(node.x, node.y, 16, "90,230,255", 0.12 + Math.sin(time * 3 + node.x) * 0.04);
        }

        ctx.fillStyle = "#090714";
        ctx.beginPath();
        ctx.arc(node.x, node.y, 8 * pulse, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = lit
          ? `rgb(${node.tint})`
          : scanning
            ? "#7ee7ff"
            : "rgba(186,170,255,0.55)";
        ctx.lineWidth = lit ? 2 : 1;
        ctx.stroke();
        ctx.lineWidth = 1;
        ctx.fillStyle = lit ? "#f7fdff" : "rgba(230,232,255,0.7)";
        ctx.font = "600 9px Geist Variable, Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(node.mark, node.x, node.y);
      });

      const breath = reduced ? 1 : 1 + Math.sin(time * (hubHot ? 3.2 : 1.4)) * (hubHot ? 0.08 : 0.04);
      glow(cx, cy, 58, hubColor, hubHot ? 0.32 : 0.18);
      ctx.fillStyle = "#090714";
      ctx.beginPath();
      ctx.arc(cx, cy, 30 * breath, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = error ? "#ff8a9b" : "#7ee7ff";
      ctx.lineWidth = hubHot ? 2 : 1;
      ctx.stroke();
      ctx.lineWidth = 1;
      ctx.fillStyle = "#f7f8ff";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = "600 10px Geist Variable, Inter, sans-serif";
      ctx.fillText("MCP", cx, cy - 6);
      ctx.fillStyle = "rgba(176,228,255,0.85)";
      ctx.font = "500 8px Geist Variable, Inter, sans-serif";
      ctx.fillText("ORCHESTRATOR", cx, cy + 8);

      if ((returning || complete) && !error) {
        const ring = returning ? burst : 1;
        ctx.beginPath();
        ctx.arc(cx, cy, 38 + ring * 42, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(126,231,255,${returning ? 0.45 * (1 - burst * 0.35) : 0.12})`;
        ctx.stroke();
      }

      glow(user.x, user.y, visNow.queryReceived ? 18 : 10, "126,231,255", visNow.queryReceived ? 0.35 : 0.12);
      ctx.fillStyle = visNow.queryReceived ? "#7ee7ff" : "#3a3658";
      ctx.beginPath();
      ctx.arc(user.x, user.y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "rgba(210,214,240,0.8)";
      ctx.font = "500 8px Geist Variable, Inter, sans-serif";
      ctx.fillText("USER", user.x, user.y + 14);
    };

    let lastStamp = 0;
    const tick = (stamp) => {
      if (!running) return;
      const dt = lastStamp ? Math.min(0.05, (stamp - lastStamp) / 1000) : 0.016;
      lastStamp = stamp;
      draw(stamp, dt);
      if (reducedQuery.matches) {
        running = false;
        return;
      }
      frame = window.requestAnimationFrame(tick);
    };
    const start = () => {
      if (running || !visible || document.hidden) return;
      running = true;
      frame = window.requestAnimationFrame(tick);
    };
    const stop = () => {
      running = false;
      window.cancelAnimationFrame(frame);
    };

    const ro = new ResizeObserver(() => {
      resize();
      if (!running) draw(0);
    });
    const io = new IntersectionObserver(
      ([entry]) => {
        visible = Boolean(entry?.isIntersecting);
        if (visible) start();
        else stop();
      },
      { threshold: 0.08 }
    );

    resize();
    draw(0);
    ro.observe(stage);
    io.observe(stage);
    const onVis = () => (document.hidden ? stop() : start());
    const onMotion = () => {
      stop();
      if (visible) start();
      else draw(0);
    };
    document.addEventListener("visibilitychange", onVis);
    reducedQuery.addEventListener("change", onMotion);
    kickRef.current = () => {
      if (reducedQuery.matches) {
        draw(performance.now(), 0);
        return;
      }
      start();
    };

    return () => {
      stop();
      ro.disconnect();
      io.disconnect();
      document.removeEventListener("visibilitychange", onVis);
      reducedQuery.removeEventListener("change", onMotion);
    };
  }, []);

  useEffect(() => {
    kickRef.current();
  }, [vis.play]);

  const caption =
    vis.play === "error"
      ? "Response returning"
      : VIS_FLOW[vis.index];

  return (
    <section className="orch-core" aria-label="MCP intelligence core">
      <div className="orch-panel-head">
        <div>
          <p className="orch-kicker">MCP Orchestrator</p>
          <h2>Live routing fabric</h2>
        </div>
        <p className="orch-core-caption" aria-live="polite">
          {caption}
        </p>
      </div>
      <ol className="orch-flow">
        {VIS_FLOW.map((label, i) => {
          const isNow = vis.play === "error" ? i === 5 : i === vis.index;
          const isLive = vis.play === "error" ? i <= 5 : i <= vis.index;
          return (
            <li
              key={label}
              className={`${isLive ? "is-live" : ""}${isNow ? " is-now" : ""}`}
            >
              {label}
            </li>
          );
        })}
      </ol>
      <div className="orch-core-stage" ref={stageRef}>
        <canvas ref={canvasRef} aria-hidden="true" />
        <svg className="orch-core-frame" viewBox="0 0 100 100" aria-hidden="true">
          <path d="M8 22 V8 H22" />
          <path d="M92 22 V8 H78" />
          <path d="M8 78 V92 H22" />
          <path d="M92 78 V92 H78" />
        </svg>
      </div>
    </section>
  );
}
