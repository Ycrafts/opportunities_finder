"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface HoverLiftProps {
  children: ReactNode;
  className?: string;
  scale?: number;
}

export function HoverLift({
  children,
  className,
  scale = 1.02,
}: HoverLiftProps) {
  return (
    <motion.div
      whileHover={{ scale, y: -4 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

