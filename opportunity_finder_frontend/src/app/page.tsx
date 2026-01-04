"use client";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ArrowRight, Sparkles, Target, Zap } from "lucide-react";
import Link from "next/link";
import { config } from "@/lib/config";
import { FadeIn } from "@/components/animations/fade-in";
import { StaggerContainer, StaggerItem } from "@/components/animations/stagger-container";
import { HoverLift } from "@/components/animations/hover-lift";
import { GradientBackground } from "@/components/animations/gradient-bg";
import { AuthSection } from "@/components/auth/auth-section";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function Home() {
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");

  useEffect(() => {
    const hash = window.location.hash;
    if (hash === "#get-started") {
      setAuthMode("signup");
      // Smooth scroll to auth section
      setTimeout(() => {
        document.getElementById("get-started")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } else if (hash === "#login") {
      setAuthMode("login");
      setTimeout(() => {
        document.getElementById("get-started")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    }
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 relative">
        {/* Hero Section */}
        <section className="container relative flex flex-col items-center justify-center gap-8 px-4 py-24 text-center sm:py-32 overflow-hidden">
          <GradientBackground />
          <FadeIn delay={0.1}>
            <motion.h1
              className="text-4xl font-bold tracking-tight sm:text-6xl lg:text-7xl relative z-10"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            >
              Find opportunities that
              <motion.span
                className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent block sm:inline"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
              >
                {" "}match your profile
              </motion.span>
            </motion.h1>
          </FadeIn>
          <FadeIn delay={0.4}>
            <p className="max-w-2xl text-lg text-muted-foreground sm:text-xl relative z-10">
              {config.app.description}
            </p>
          </FadeIn>
          <FadeIn delay={0.6}>
            <div className="flex flex-col gap-4 sm:flex-row relative z-10">
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <Button
                  size="lg"
                  className="text-base"
                  onClick={() => {
                    setAuthMode("signup");
                    document.getElementById("get-started")?.scrollIntoView({ behavior: "smooth" });
                  }}
                >
                  Get Started
                </Button>
              </motion.div>
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <Button size="lg" variant="outline" className="text-base group" asChild>
                  <Link href="#learn-more">
                    Learn More
                    <motion.span
                      className="inline-block ml-2"
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ArrowRight className="h-4 w-4" />
                    </motion.span>
                  </Link>
                </Button>
              </motion.div>
            </div>
          </FadeIn>
        </section>

        {/* Features Section */}
        <section className="border-t bg-muted/30 py-24">
          <div className="container px-4">
            <FadeIn>
              <div className="mb-16 text-center">
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                  Everything you need. Nothing you don't
                </h2>
                <p className="mt-4 text-lg text-muted-foreground">
                  Opportunity matching and career insights in one place. Experience a flexible
                  toolkit that makes every task feel like a breeze.
                </p>
              </div>
            </FadeIn>
            <StaggerContainer className="grid gap-8 md:grid-cols-3">
              <StaggerItem>
                <HoverLift>
                  <Card className="h-full transition-all duration-300 hover:shadow-lg">
                    <CardHeader>
                      <motion.div
                        className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10"
                        whileHover={{ rotate: [0, -10, 10, -10, 0] }}
                        transition={{ duration: 0.5 }}
                      >
                        <Target className="h-6 w-6 text-primary" />
                      </motion.div>
                      <CardTitle>Smart Matching</CardTitle>
                      <CardDescription>
                        AI-powered matching that understands your skills, experience, and
                        preferences to surface the perfect opportunities.
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </HoverLift>
              </StaggerItem>
              <StaggerItem>
                <HoverLift>
                  <Card className="h-full transition-all duration-300 hover:shadow-lg">
                    <CardHeader>
                      <motion.div
                        className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10"
                        whileHover={{ rotate: [0, -10, 10, -10, 0] }}
                        transition={{ duration: 0.5 }}
                      >
                        <Zap className="h-6 w-6 text-primary" />
                      </motion.div>
                      <CardTitle>Real-time Updates</CardTitle>
                      <CardDescription>
                        Get instant notifications when new opportunities match your profile. Never
                        miss a chance to advance your career.
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </HoverLift>
              </StaggerItem>
              <StaggerItem>
                <HoverLift>
                  <Card className="h-full transition-all duration-300 hover:shadow-lg">
                    <CardHeader>
                      <motion.div
                        className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10"
                        whileHover={{ rotate: [0, -10, 10, -10, 0] }}
                        transition={{ duration: 0.5 }}
                      >
                        <Sparkles className="h-6 w-6 text-primary" />
                      </motion.div>
                      <CardTitle>AI-Powered Tools</CardTitle>
                      <CardDescription>
                        Generate cover letters, analyze skill gaps, and get personalized insights
                        to help you land your dream opportunity.
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </HoverLift>
              </StaggerItem>
            </StaggerContainer>
          </div>
        </section>

        {/* Auth Section */}
        <section id="get-started" className="border-t bg-muted/30 py-24">
          <div className="container px-4">
            <FadeIn>
              <div className="mb-12 text-center">
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                  Get Started Today
                </h2>
                <p className="mt-4 text-lg text-muted-foreground">
                  Join thousands of professionals who have found their perfect match.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.2}>
              <AuthSection defaultMode={authMode} />
            </FadeIn>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container flex flex-col items-center justify-between gap-4 px-4 sm:flex-row">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} Opportunity Finder. All rights reserved.
          </p>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <Link href="#" className="hover:text-foreground">
              Privacy
            </Link>
            <Link href="#" className="hover:text-foreground">
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
