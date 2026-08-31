"use client";

type QuantumCloudLoaderProps = {
  className?: string;
};

export default function QuantumCloudLoader({
  className = "",
}: QuantumCloudLoaderProps) {
  return (
    <div
      className={`flex min-h-[200px] items-center justify-center overflow-hidden ${className}`.trim()}
    >
      <div className="relative isolate flex h-24 w-44 items-center justify-center">
        {/* Inner particle */}
        <div className="absolute z-30 h-4 w-4 animate-quantum-red">
          <div className="h-full w-full rounded-full bg-zinc-300 shadow-[0_0_12px_rgba(255,255,255,0.45),0_0_24px_rgba(255,255,255,0.18)]" />
        </div>

        {/* Outer particle */}
        <div className="absolute z-10 h-6 w-6 animate-quantum-blue">
          <div className="h-full w-full rounded-full bg-zinc-500 shadow-[0_0_16px_rgba(255,255,255,0.28),0_0_30px_rgba(255,255,255,0.1)]" />
        </div>

        {/* Center particle */}
        <div className="absolute z-40 h-5 w-5 animate-quantum-yellow">
          <div className="h-full w-full rounded-full bg-white shadow-[0_0_14px_rgba(255,255,255,0.55),0_0_26px_rgba(255,255,255,0.2)]" />
        </div>

        {/* Slow orbital particle */}
        <div className="absolute z-0 h-3.5 w-3.5 animate-quantum-green">
          <div className="h-full w-full rounded-full bg-zinc-400 shadow-[0_0_12px_rgba(255,255,255,0.35),0_0_24px_rgba(255,255,255,0.12)]" />
        </div>
      </div>

      <style>{`
        @keyframes quantum-red {
          0% {
            transform: translate3d(-46px, 7px, 0) scale(0.72);
            opacity: 0.45;
          }

          25% {
            transform: translate3d(-23px, -7px, 0) scale(0.95);
            opacity: 0.78;
          }

          50% {
            transform: translate3d(46px, 0, 0) scale(1.18);
            opacity: 1;
          }

          75% {
            transform: translate3d(23px, 7px, 0) scale(0.95);
            opacity: 0.78;
          }

          100% {
            transform: translate3d(-46px, 7px, 0) scale(0.72);
            opacity: 0.45;
          }
        }

        .animate-quantum-red {
          animation:
            quantum-red
            3.8s
            cubic-bezier(0.37, 0, 0.63, 1)
            infinite;
          will-change: transform, opacity;
        }

        @keyframes quantum-blue {
          0% {
            transform: translate3d(38px, -4px, 0) scale(1);
            opacity: 0.95;
          }

          25% {
            transform: translate3d(19px, 7px, 0) scale(0.88);
            opacity: 0.72;
          }

          50% {
            transform: translate3d(-38px, 3px, 0) scale(0.68);
            opacity: 0.42;
          }

          75% {
            transform: translate3d(-19px, -7px, 0) scale(0.88);
            opacity: 0.72;
          }

          100% {
            transform: translate3d(38px, -4px, 0) scale(1);
            opacity: 0.95;
          }
        }

        .animate-quantum-blue {
          animation:
            quantum-blue
            5.6s
            cubic-bezier(0.37, 0, 0.63, 1)
            infinite;
          will-change: transform, opacity;
        }

        @keyframes quantum-yellow {
          0% {
            transform: translate3d(-27px, 2px, 0) scale(0.82);
            opacity: 0.65;
          }

          20% {
            transform: translate3d(-17px, -5px, 0) scale(0.94);
            opacity: 0.82;
          }

          50% {
            transform: translate3d(27px, 0, 0) scale(1.08);
            opacity: 1;
          }

          80% {
            transform: translate3d(17px, 5px, 0) scale(0.94);
            opacity: 0.82;
          }

          100% {
            transform: translate3d(-27px, 2px, 0) scale(0.82);
            opacity: 0.65;
          }
        }

        .animate-quantum-yellow {
          animation:
            quantum-yellow
            3.1s
            cubic-bezier(0.37, 0, 0.63, 1)
            infinite;
          will-change: transform, opacity;
        }

        @keyframes quantum-green {
          0% {
            transform: translate3d(64px, 6px, 0) scale(0.52);
            opacity: 0.25;
          }

          20% {
            transform: translate3d(43px, -5px, 0) scale(0.68);
            opacity: 0.45;
          }

          50% {
            transform: translate3d(0, 3px, 0) scale(1);
            opacity: 0.9;
          }

          80% {
            transform: translate3d(-43px, -5px, 0) scale(0.68);
            opacity: 0.45;
          }

          100% {
            transform: translate3d(-64px, 6px, 0) scale(0.52);
            opacity: 0.25;
          }
        }

        .animate-quantum-green {
          animation:
            quantum-green
            6.4s
            cubic-bezier(0.37, 0, 0.63, 1)
            infinite alternate;
          will-change: transform, opacity;
        }

        @media (prefers-reduced-motion: reduce) {
          .animate-quantum-red,
          .animate-quantum-blue,
          .animate-quantum-yellow,
          .animate-quantum-green {
            animation: none;
          }
        }
      `}</style>
    </div>
  );
}
