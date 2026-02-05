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
import { CursorTrail } from "@/components/animations/cursor-trail";
import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/auth-context";
import { LayoutDashboard } from "lucide-react";
import { AnimatePresence } from "framer-motion";



export default function Home() {
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const { isAuthenticated, isLoading } = useAuth();

  const scrollToAuthSection = (mode: "login" | "signup") => {
    const authSection = document.getElementById("get-started");
    if (!authSection) return;
    const offset = 180;
    const top = authSection.getBoundingClientRect().top + window.scrollY + offset;
    window.scrollTo({ top, behavior: "smooth" });
    window.dispatchEvent(new CustomEvent("auth-mode-change", { detail: mode }));
  };

  useEffect(() => {
    // Only handle hash navigation if user is not authenticated
    if (!isAuthenticated && !isLoading) {
      const hash = window.location.hash;
      if (hash === "#get-started") {
        setAuthMode("signup");
        setTimeout(() => {
          scrollToAuthSection("signup");
        }, 100);
      } else if (hash === "#login") {
        setAuthMode("login");
        setTimeout(() => {
          scrollToAuthSection("login");
        }, 100);
      }
    }
  }, [isAuthenticated, isLoading]);
  const videos = [
    "video/herobg1.mp4", 
    "video/herobg2.mp4", // Add your extra video paths here
    "video/herobg3.mp4"
  ];
  const [videoIndex, setVideoIndex] = useState(0);

  const handleVideoEnd = () => {
    // Moves to next video, loops back to 0 at the end
    setVideoIndex((prev) => (prev + 1) % videos.length);
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      handleVideoEnd();
    }, 5000); // 5 seconds

    return () => clearTimeout(timer);
  }, [videoIndex]);

  // Feature cards hover cycle: 0=Smart, 1=Real-time (default center), 2=AI-Powered
  const [centerIdx, setCenterIdx] = useState(1);
  const cycleRef = useRef<number | null>(null);
  const onFeaturesEnter = () => {
    if (cycleRef.current) return;
    cycleRef.current = window.setInterval(() => {
      setCenterIdx((c) => (c === 1 ? 2 : c === 2 ? 0 : 1));
    }, 900);
  };
  const onFeaturesLeave = () => {
    if (cycleRef.current) {
      window.clearInterval(cycleRef.current);
      cycleRef.current = null;
    }
    setCenterIdx(1);
  };
  const wrapCls = (i: number) => {
    const rightOfCenter = (centerIdx + 1) % 3;
    if (i === centerIdx) return "md:order-2 md:scale-110 md:z-20";
    if (i === rightOfCenter) return "md:order-3 md:scale-95 md:z-10";
    return "md:order-1 md:scale-95 md:z-10";
  };

  return (
    <div className="flex min-h-screen flex-col">
      <CursorTrail />
      <Header />
      <main className="flex-1 relative">
        {/* Hero Section */}
        <section className="relative flex min-h-screen w-full flex-col items-center md:items-start justify-center gap-8 px-4 py-24 text-center md:text-left overflow-hidden">
          
          <div className="absolute inset-0 -z-10">
            <AnimatePresence>
              <motion.video
                key={videos[videoIndex]} // Required for React to swap videos
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 1.5 }} // Smooth 1.5s fade between clips
                autoPlay
                muted
                playsInline
                preload="auto"
                className="absolute inset-0 h-full w-full object-cover"
              >
              <source src={videos[videoIndex]} type="video/mp4" />
              </motion.video>
            </AnimatePresence>
            
            
            <div className="absolute inset-0 bg-black/20" />
            <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-black/40 to-transparent pointer-events-none" /> 
          </div>

        <div className="container relative z-10 flex flex-col items-start text-left max-w-5xl self-start pl-4 md:pl-8 lg:pl-16">
        <FadeIn delay={0.1}>
          <motion.h1
            className="text-2xl sm:text-4xl lg:text-7xl font-black tracking-tighter text-white leading-[1.1] uppercase"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          >
            Match.<br />
            Connect. <span className="text-[#64e781]">Succeed.</span><br />
            Advance.
          </motion.h1>
        </FadeIn>


          <FadeIn delay={0.4}>
            <p className="max-w-2xl text-lg text-white/80 sm:text-xl relative z-10">
              {config.app.description}
            </p>
          </FadeIn>

          <FadeIn delay={0.6}>
            <div className="flex flex-col gap-4 sm:flex-row relative z-10 mt-10">
              {isAuthenticated ? (
                <Button size="lg" className="text-base gap-2 bg-[#0f9b57] hover:bg-[#0d884d]" asChild>
                    <Link href="/dashboard">Go to Dashboard</Link>
                </Button>
              ) : (
                <>
                  <Button
                    size="lg"
                    className="text-base bg-[#0f9b57] hover:bg-[#0d884d]"
                    onClick={() => {
                      setAuthMode("signup");
                      scrollToAuthSection("signup");
                    }}
                  >
                    Get Started
                  </Button>
                  <Button
                    size="lg"
                    variant="outline"
                    className="text-base bg-white/10 text-white hover:bg-white/20 border-white/20"
                    asChild
                  >
                    <Link href="/opportunities">Browse Opportunities</Link>
                  </Button>
                </>
              )}
            </div>
          </FadeIn>
          </div>
        </section>

        {/* Features Section */}
        <section className="border-t bg-muted/30 py-24">
          <div className="container px-4">
            <FadeIn>
              <div className="mb-16 text-center">
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                  The Signal in the Noise
                </h2>
                <p className="mt-4 text-lg text-muted-foreground">
                  Personalized matches and career insights in one intelligent hub. Eliminate search fatigue and find exactly what fits your profile.
                </p>
              </div>
            </FadeIn>
            <div onMouseEnter={onFeaturesEnter} onMouseLeave={onFeaturesLeave} className="md:flex md:justify-center md:items-stretch md:-space-x-6">
              <StaggerContainer className="grid gap-6 md:flex md:gap-0">
                <div className={`transition-all duration-300 md:basis-[22rem] md:flex-shrink-0 ${wrapCls(0)}`}>
                  <StaggerItem>
                    <HoverLift>
                      <Card className="h-full transition-all duration-300 hover:shadow-lg bg-background/70 backdrop-blur-sm">
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
                </div>
                <div className={`transition-all duration-300 md:basis-[22rem] md:flex-shrink-0 ${wrapCls(1)}`}>
                  <StaggerItem>
                    <HoverLift>
                      <Card className="h-full transition-all duration-300 hover:shadow-lg bg-background/70 backdrop-blur-sm">
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
                </div>
                <div className={`transition-all duration-300 md:basis-[22rem] md:flex-shrink-0 ${wrapCls(2)}`}>
                  <StaggerItem>
                    <HoverLift>
                      <Card className="h-full transition-all duration-300 hover:shadow-lg bg-background/70 backdrop-blur-sm">
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
                </div>
              </StaggerContainer>
            </div>
          </div>
        </section>

        

        {/* Logo Slider Section */}
        <section className="py-16">
          <div className="container px-4">
            <div className="mb-6 text-center">
              <h2 className="text-xl font-semibold text-foreground/80">Jobs from Leading Companies</h2>
            </div>
            <div className="relative overflow-hidden">
              {/* Track */}
              <motion.div
                className="flex will-change-transform"
                initial={{ x: 0 }}
                animate={{ x: ["0%", "-50%"] }}
                transition={{ duration: 30, ease: "linear", repeat: Infinity }}
              >
                {/* One sequence */}
                <div className="flex items-center gap-20 min-w-max pr-20">
                  <img src="/logos/ethiojobs.jpg" alt="Ethiojobs" className="h-20 w-auto opacity-80 hover:opacity-100 transition-opacity" />
                  <img src="/logos/afriwork.webp" alt="Afriwork" className="h-20 w-auto opacity-80 hover:opacity-100 transition-opacity" />
                  <img src="/logos/brightschol.jpg" alt="Partner" className="h-20 w-auto opacity-80 hover:opacity-100 transition-opacity" />
                  <img src="/logos/dereja.jpg" alt="Ethiojobs" className="h-20 w-auto opacity-80 hover:opacity-100 transition-opacity" />
                  <img src="/logos/ethvac.jpg" alt="Afriwork" className="h-20 w-auto opacity-80 hover:opacity-100 transition-opacity" />
                  <img src="/logos/opp4all.jpg" alt="Partner" className="h-20 w-auto opacity-80 hover:opacity-100 transition-opacity" />
                  <img src="/logos/opp4youth.jpg" alt="Partner" className="h-20 w-auto opacity-80 hover:opacity-100 transition-opacity" />
                  <img src="/logos/wwr.jpg" alt="Partner" className="h-20 w-auto opacity-80 hover:opacity-100 transition-opacity" />
                </div>
                {/* Duplicate for seamless loop */}
                <div className="flex items-center gap-20 min-w-max pr-20" aria-hidden>
                  <img src="/logos/ethiojobs.jpg" alt="" className="h-20 w-auto opacity-80" />
                  <img src="/logos/afriwork.webp" alt="" className="h-20 w-auto opacity-80" />
                  <img src="/logos/brightschol.jpg" alt="" className="h-20 w-auto opacity-80" />
                  <img src="/logos/dereja.jpg" alt="" className="h-20 w-auto opacity-80" />
                  <img src="/logos/ethvac.jpg" alt="" className="h-20 w-auto opacity-80" />
                  <img src="/logos/opp4all.jpg" alt="" className="h-20 w-auto opacity-80" />
                  <img src="/logos/opp4youth.jpg" alt="" className="h-20 w-auto opacity-80" />
                  <img src="/logos/wwr.jpg" alt="" className="h-20 w-auto opacity-80" />
                </div>
              </motion.div>
              {/* Edge fade helpers (optional subtle) */}
              <div className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-background to-transparent" />
              <div className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-background to-transparent" />
            </div>
          </div>
        </section>

        {/* Auth Section */}
        {!isAuthenticated && (
          <section id="get-started" className="border-t bg-muted/30 py-24">
            <div className="container px-4">
              <FadeIn>
                <div className="mb-12 text-center">
                  <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                    Get Started Today
                  </h2>
                  <p className="mt-4 text-lg text-muted-foreground">
                    Join a smarter way to find jobs and scholarships. Built for precision. Powered by AI.
                  </p>
                </div>
              </FadeIn>
              {/* 4-step process timeline (moved here) */}
              <div className="py-10">
                <div className="relative">
                  <div className="hidden md:block absolute top-6 left-[12.5%] right-[12.5%] h-px bg-gray-300" />
                  <ul className="grid grid-cols-1 md:grid-cols-4 gap-10 md:gap-6">
                    <li className="flex flex-col items-center text-center">
                      <div className="z-10 flex h-12 w-12 items-center justify-center rounded-full" style={{ backgroundColor: '#0f9b57' }}>
                        <span className="text-white font-semibold">1</span>
                      </div>
                      <p className="mt-4 text-sm md:text-base">Register and upload your CV so our AI can automatically extract your skills and build your professional digital profile in seconds.</p>
                    </li>
                    <li className="flex flex-col items-center text-center">
                      <div className="z-10 flex h-12 w-12 items-center justify-center rounded-full" style={{ backgroundColor: '#0f9b57' }}>
                        <span className="text-white font-semibold">2</span>
                      </div>
                      <p className="mt-4 text-sm md:text-base">Our automated engine harvests jobs and scholarships to centralize every relevant opportunity in one place.</p>
                    </li>
                    <li className="flex flex-col items-center text-center">
                      <div className="z-10 flex h-12 w-12 items-center justify-center rounded-full" style={{ backgroundColor: '#0f9b57' }}>
                        <span className="text-white font-semibold">3</span>
                      </div>
                      <p className="mt-4 text-sm md:text-base">Review your personalized match scores and use our AI analysis to identify exactly which skills you are missing for your target role.</p>
                    </li>
                    <li className="flex flex-col items-center text-center">
                      <div className="z-10 flex h-12 w-12 items-center justify-center rounded-full" style={{ backgroundColor: '#0f9b57' }}>
                        <span className="text-white font-semibold">4</span>
                      </div>
                      <p className="mt-4 text-sm md:text-base">Receive real-time alerts and use our generative tools to draft tailored cover letters that help you stand out to recruiters.</p>
                    </li>
                  </ul>
                </div>
              </div>
              <FadeIn delay={0.2}>
                <div className="mt-6">
                  <AuthSection defaultMode={authMode} />
                </div>
              </FadeIn>
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container flex flex-col items-center justify-between gap-4 px-4 sm:flex-row">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} Findra. All rights reserved.
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
