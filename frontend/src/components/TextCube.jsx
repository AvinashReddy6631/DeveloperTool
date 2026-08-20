import { useEffect, useRef } from "react";

const faces = [
  { text: "MCP", className: "front" },
  { text: "AGENT", className: "back" },
  { text: "ORCHESTRATOR", className: "right" },
  { text: "MCP", className: "left" },
  { text: "AI", className: "top" },
  { text: "AI", className: "bottom" },
];

function TextCube() {
  const cubeRef = useRef(null);
  const targetRotation = useRef({ x: -15, y: 25 });
  const currentRotation = useRef({ x: -15, y: 25 });
  const animationFrame = useRef(null);

  useEffect(() => {
    const cube = cubeRef.current;

    if (!cube) return;

    const animate = () => {
      currentRotation.current.x +=
        (targetRotation.current.x - currentRotation.current.x) * 0.08;

      currentRotation.current.y +=
        (targetRotation.current.y - currentRotation.current.y) * 0.08;

      cube.style.transform = `
        rotateX(${currentRotation.current.x}deg)
        rotateY(${currentRotation.current.y}deg)
      `;

      animationFrame.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrame.current);
    };
  }, []);

  const handleMouseMove = (event) => {
    const { innerWidth, innerHeight } = window;

    const x = event.clientX / innerWidth - 0.5;
    const y = event.clientY / innerHeight - 0.5;

    targetRotation.current = {
      x: -y * 45,
      y: x * 60,
    };
  };

  const handleMouseLeave = () => {
    targetRotation.current = {
      x: -15,
      y: 25,
    };
  };

  return (
    <div
      className="cube-scene"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div ref={cubeRef} className="text-cube">
        {faces.map((face, index) => (
          <div
            key={index}
            className={`cube-face ${face.className}`}
          >
            {face.text}
          </div>
        ))}
      </div>
    </div>
  );
}

export default TextCube;