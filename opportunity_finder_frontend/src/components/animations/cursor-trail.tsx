"use client";

import { useEffect, useRef } from "react";

export function CursorTrail() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let particleId = 0;

    const createParticle = (x: number, y: number) => {
      const particle = document.createElement("div");
      particle.className = "animate-particle";

      // Random velocity for spread effect
      const angle = Math.random() * Math.PI * 2;
      const velocity = 50 + Math.random() * 100;
      const vx = Math.cos(angle) * velocity;
      const vy = Math.sin(angle) * velocity;

      particle.style.setProperty("--vx", `${vx}px`);
      particle.style.setProperty("--vy", `${vy}px`);
      particle.style.left = `${x}px`;
      particle.style.top = `${y}px`;

      // Light, subtle styling
      particle.style.width = "4px";
      particle.style.height = "4px";
      particle.style.borderRadius = "50%";
      particle.style.background = "currentColor";
      particle.style.color = "hsl(var(--primary))";
      particle.style.position = "fixed";
      particle.style.pointerEvents = "none";
      particle.style.zIndex = "9999";

      container.appendChild(particle);

      // Clean up after animation
      setTimeout(() => {
        particle.remove();
      }, 1000);
    };

    let lastTime = 0;
    const throttleDelay = 16; // ~60fps

    const handleMouseMove = (e: MouseEvent) => {
      const now = Date.now();
      if (now - lastTime < throttleDelay) return;
      lastTime = now;

      // Only create particles occasionally for lightness
      if (Math.random() > 0.3) return;

      createParticle(e.clientX, e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="pointer-events-none fixed inset-0 z-[9999]"
    />
  );
}
