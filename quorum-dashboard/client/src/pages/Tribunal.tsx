/*
 * DESIGN: Neural Network Interface - Philosopher Tribunal Page
 * - 6 philosophers in circular arrangement
 * - Chain deliberation visualization
 * - Observer consensus mechanism
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { Users, Eye, MessageCircle, Scale, Sparkles } from "lucide-react";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface Philosopher {
  id: string;
  name: string;
  fullName: string;
  era: string;
  tradition: string;
  style: string;
  color: string;
  bgColor: string;
  keyConcepts: string[];
}

const philosophers: Philosopher[] = [
  {
    id: "hume",
    name: "Hume",
    fullName: "David Hume",
    era: "1711-1776",
    tradition: "Scottish Enlightenment",
    style: "Empirical skeptic - demands evidence, questions causation",
    color: "text-[oklch(0.7_0.15_240)]",
    bgColor: "bg-[oklch(0.7_0.15_240)]",
    keyConcepts: ["Empiricism", "Skepticism", "Causation", "Is-Ought"],
  },
  {
    id: "popper",
    name: "Popper",
    fullName: "Karl Popper",
    era: "1902-1994",
    tradition: "Critical Rationalism",
    style: "Falsificationist - seeks what can be disproven",
    color: "text-[oklch(0.7_0.18_150)]",
    bgColor: "bg-[oklch(0.7_0.18_150)]",
    keyConcepts: ["Falsifiability", "Demarcation", "Conjectures", "Open Society"],
  },
  {
    id: "quine",
    name: "Quine",
    fullName: "W.V.O. Quine",
    era: "1908-2000",
    tradition: "Analytic Philosophy",
    style: "Naturalist - dissolves distinctions, challenges definitions",
    color: "text-[oklch(0.75_0.18_195)]",
    bgColor: "bg-[oklch(0.75_0.18_195)]",
    keyConcepts: ["Holism", "Indeterminacy", "Naturalized Epistemology"],
  },
  {
    id: "arendt",
    name: "Arendt",
    fullName: "Hannah Arendt",
    era: "1906-1975",
    tradition: "Political Theory",
    style: "Political theorist - examines power, propaganda, banal evil",
    color: "text-[oklch(0.7_0.18_25)]",
    bgColor: "bg-[oklch(0.7_0.18_25)]",
    keyConcepts: ["Banality of Evil", "Totalitarianism", "Public Sphere"],
  },
  {
    id: "zhuangzi",
    name: "Zhuangzi",
    fullName: "Zhuangzi (莊子)",
    era: "369-286 BCE",
    tradition: "Daoist Philosophy",
    style: "Daoist sage - seeks paradox, values uselessness",
    color: "text-[oklch(0.75_0.15_85)]",
    bgColor: "bg-[oklch(0.75_0.15_85)]",
    keyConcepts: ["Wu Wei", "Transformation", "Relativity", "Spontaneity"],
  },
  {
    id: "khaldun",
    name: "Ibn Khaldun",
    fullName: "Ibn Khaldun (ابن خلدون)",
    era: "1332-1406",
    tradition: "Islamic Philosophy",
    style: "Civilizational analyst - tracks cycles, material forces",
    color: "text-[oklch(0.7_0.15_55)]",
    bgColor: "bg-[oklch(0.7_0.15_55)]",
    keyConcepts: ["Asabiyyah", "Umran", "Civilizational Cycles"],
  },
];

export default function Tribunal() {
  const [query, setQuery] = useState("");
  const [selectedPhilosopher, setSelectedPhilosopher] = useState<Philosopher | null>(null);
  const [isDeliberating, setIsDeliberating] = useState(false);
  const [deliberationStep, setDeliberationStep] = useState(0);

  const simulateDeliberation = () => {
    if (!query.trim()) return;
    setIsDeliberating(true);
    setDeliberationStep(0);
    
    // Simulate chain deliberation
    const interval = setInterval(() => {
      setDeliberationStep((prev) => {
        if (prev >= 6) {
          clearInterval(interval);
          setIsDeliberating(false);
          return prev;
        }
        return prev + 1;
      });
    }, 800);
  };

  return (
    <Layout>
      <div className="container py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-2 rounded-xl bg-accent/20">
              <Users className="w-6 h-6 text-accent" />
            </div>
            <span className="text-sm font-medium text-accent uppercase tracking-wide">
              Truth Forensics Engine
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            The Philosopher Tribunal
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Six philosophical minds chain together to analyze claims. The Observer 
            enforces silence when consensus exceeds 92%.
          </p>
        </motion.div>

        {/* Philosopher Circle */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="relative max-w-4xl mx-auto mb-16"
        >
          {/* Background Image */}
          <div className="aspect-square relative">
            <img
              src="/images/philosopher-tribunal.png"
              alt="Philosopher Tribunal"
              className="w-full h-full object-cover rounded-3xl opacity-30"
            />
            
            {/* Philosopher Cards Overlay */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative w-[90%] h-[90%]">
                {/* Observer in Center */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.5 }}
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10"
                >
                  <div className="neural-card p-6 text-center">
                    <Eye className="w-10 h-10 mx-auto mb-2 text-primary" />
                    <div className="font-bold">Observer</div>
                    <div className="text-xs text-muted-foreground">Threshold: 92%</div>
                  </div>
                </motion.div>

                {/* Philosophers around the circle */}
                {philosophers.map((philosopher, index) => {
                  const angle = (index / 6) * 2 * Math.PI - Math.PI / 2;
                  const radius = 42; // percentage
                  const x = 50 + radius * Math.cos(angle);
                  const y = 50 + radius * Math.sin(angle);
                  const isActive = deliberationStep > index;
                  
                  return (
                    <motion.div
                      key={philosopher.id}
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ 
                        opacity: 1, 
                        scale: 1,
                        boxShadow: isActive ? `0 0 30px ${philosopher.bgColor.replace('bg-', '')}` : 'none'
                      }}
                      transition={{ delay: 0.3 + index * 0.1 }}
                      onClick={() => setSelectedPhilosopher(
                        selectedPhilosopher?.id === philosopher.id ? null : philosopher
                      )}
                      className={`absolute cursor-pointer transform -translate-x-1/2 -translate-y-1/2
                                ${isActive ? 'neural-glow' : ''}`}
                      style={{ left: `${x}%`, top: `${y}%` }}
                    >
                      <div className={`neural-card p-4 text-center min-w-[120px] transition-all
                                    ${selectedPhilosopher?.id === philosopher.id ? 'ring-2 ring-primary' : ''}
                                    ${isActive ? 'scale-110' : ''}`}>
                        <div className={`w-10 h-10 rounded-full ${philosopher.bgColor} mx-auto mb-2 
                                      flex items-center justify-center text-white font-bold`}>
                          {philosopher.name[0]}
                        </div>
                        <div className={`font-bold ${philosopher.color}`}>{philosopher.name}</div>
                        <div className="text-xs text-muted-foreground">{philosopher.era}</div>
                      </div>
                    </motion.div>
                  );
                })}

                {/* Connection Lines */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                  {philosophers.map((_, index) => {
                    const nextIndex = (index + 1) % 6;
                    const angle1 = (index / 6) * 2 * Math.PI - Math.PI / 2;
                    const angle2 = (nextIndex / 6) * 2 * Math.PI - Math.PI / 2;
                    const radius = 42;
                    const x1 = 50 + radius * Math.cos(angle1);
                    const y1 = 50 + radius * Math.sin(angle1);
                    const x2 = 50 + radius * Math.cos(angle2);
                    const y2 = 50 + radius * Math.sin(angle2);
                    const isActive = deliberationStep > index;
                    
                    return (
                      <line
                        key={index}
                        x1={`${x1}%`}
                        y1={`${y1}%`}
                        x2={`${x2}%`}
                        y2={`${y2}%`}
                        className={`synapse-line transition-all duration-500 ${
                          isActive ? 'opacity-100' : 'opacity-20'
                        }`}
                        strokeDasharray={isActive ? "0" : "5,5"}
                      />
                    );
                  })}
                </svg>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Selected Philosopher Details */}
        {selectedPhilosopher && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-2xl mx-auto mb-12"
          >
            <div className="neural-card p-8">
              <div className="flex items-start gap-6">
                <div className={`w-16 h-16 rounded-2xl ${selectedPhilosopher.bgColor} 
                              flex items-center justify-center text-white text-2xl font-bold shrink-0`}>
                  {selectedPhilosopher.name[0]}
                </div>
                <div className="flex-1">
                  <h3 className={`text-2xl font-bold ${selectedPhilosopher.color}`}>
                    {selectedPhilosopher.fullName}
                  </h3>
                  <div className="text-sm text-muted-foreground mb-2">
                    {selectedPhilosopher.era} • {selectedPhilosopher.tradition}
                  </div>
                  <p className="text-muted-foreground mb-4">{selectedPhilosopher.style}</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedPhilosopher.keyConcepts.map((concept) => (
                      <span
                        key={concept}
                        className={`px-3 py-1 text-sm rounded-full bg-opacity-20 ${selectedPhilosopher.bgColor} ${selectedPhilosopher.color}`}
                      >
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Query Input */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="max-w-2xl mx-auto"
        >
          <div className="neural-card p-8">
            <div className="flex items-center gap-3 mb-4">
              <MessageCircle className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-bold">Submit a Claim for Deliberation</h3>
            </div>
            <Textarea
              placeholder="Enter a claim or question for the tribunal to analyze..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="mb-4 bg-background/50 min-h-[100px]"
            />
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                {isDeliberating ? (
                  <span className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 animate-pulse text-primary" />
                    Philosopher {Math.min(deliberationStep, 6)} of 6 deliberating...
                  </span>
                ) : deliberationStep >= 6 ? (
                  <span className="flex items-center gap-2 text-primary">
                    <Scale className="w-4 h-4" />
                    Deliberation complete
                  </span>
                ) : (
                  "The tribunal will chain through all 6 perspectives"
                )}
              </div>
              <Button
                onClick={simulateDeliberation}
                disabled={isDeliberating || !query.trim()}
                className="bg-primary hover:bg-primary/90"
              >
                {isDeliberating ? "Deliberating..." : "Begin Deliberation"}
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Philosopher Grid */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-16"
        >
          <h2 className="text-2xl font-bold mb-6 text-center">The Six Minds</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {philosophers.map((philosopher, index) => (
              <motion.div
                key={philosopher.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                className="neural-card p-6"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className={`w-12 h-12 rounded-xl ${philosopher.bgColor} 
                                flex items-center justify-center text-white font-bold text-lg`}>
                    {philosopher.name[0]}
                  </div>
                  <div>
                    <h3 className={`font-bold ${philosopher.color}`}>{philosopher.fullName}</h3>
                    <div className="text-xs text-muted-foreground">{philosopher.tradition}</div>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-4">{philosopher.style}</p>
                <div className="flex flex-wrap gap-1">
                  {philosopher.keyConcepts.slice(0, 3).map((concept) => (
                    <span
                      key={concept}
                      className="px-2 py-0.5 text-xs rounded-full bg-primary/10 text-primary"
                    >
                      {concept}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </Layout>
  );
}
