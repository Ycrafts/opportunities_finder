"use client";

import { motion } from "framer-motion";

export function GradientBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <motion.div
        className="absolute -left-1/2 -top-1/2 h-[800px] w-[800px] rounded-full bg-primary/20 blur-3xl"
        animate={{
          x: [0, 100, 0],
          y: [0, 50, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear",
        }}
      />
      <motion.div
        className="absolute -right-1/2 -bottom-1/2 h-[600px] w-[600px] rounded-full bg-primary/10 blur-3xl"
        animate={{
          x: [0, -80, 0],
          y: [0, -40, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "linear",
        }}
      />
    </div>
  );
}

