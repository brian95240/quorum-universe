/*
 * DESIGN: Neural Network Interface - Biopunk/Organic Tech
 * - Deep teal background with bioluminescent cyan accents
 * - Organic, curved shapes - cell-membrane styled cards
 * - Pulsing neural pathway connections
 */

import { Link } from "wouter";
import { motion } from "framer-motion";
import { 
  Brain, 
  Network, 
  Users, 
  Activity, 
  Zap,
  GitBranch,
  Database,
  Cpu,
  Hexagon
} from "lucide-react";
import Layout from "@/components/Layout";

const stats = [
  { label: "Archetypes", value: "26", icon: Brain, color: "text-[oklch(0.75_0.18_195)]" },
  { label: "Philosophers", value: "6", icon: Users, color: "text-[oklch(0.65_0.15_25)]" },
  { label: "Corpus Size", value: "846 GB", icon: Database, color: "text-[oklch(0.6_0.12_150)]" },
  { label: "Synergy Clusters", value: "15", icon: GitBranch, color: "text-[oklch(0.7_0.14_280)]" },
];

const quickLinks = [
  {
    title: "Archetypes",
    description: "Explore 26 institutional knowledge archetypes arranged in hexagonal rings",
    href: "/archetypes",
    icon: Brain,
    gradient: "from-[oklch(0.75_0.18_195)] to-[oklch(0.6_0.15_195)]",
  },
  {
    title: "Philosopher Tribunal",
    description: "6-philosopher truth forensics: Hume, Popper, Quine, Arendt, Zhuangzi, Ibn Khaldun",
    href: "/tribunal",
    icon: Users,
    gradient: "from-[oklch(0.65_0.15_25)] to-[oklch(0.55_0.12_25)]",
  },
  {
    title: "Hex-Ring Synergies",
    description: "Optimized ring collapse showing face-to-face knowledge alignments",
    href: "/synergies",
    icon: Hexagon,
    gradient: "from-[oklch(0.6_0.12_150)] to-[oklch(0.5_0.1_150)]",
  },
  {
    title: "System Metrics",
    description: "Real-time performance, cache efficiency, and network health",
    href: "/metrics",
    icon: Activity,
    gradient: "from-[oklch(0.7_0.14_280)] to-[oklch(0.6_0.12_280)]",
  },
];

export default function Home() {
  return (
    <Layout>
      {/* Hero Section */}
      <section className="relative min-h-[70vh] flex items-center overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-40"
          style={{ backgroundImage: "url('/images/hero-neural-network.png')" }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-background/60 to-background" />
        
        <div className="container relative z-10 py-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="max-w-3xl"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-xl bg-primary/20 neural-glow">
                <Zap className="w-6 h-6 text-primary" />
              </div>
              <span className="text-sm font-medium text-primary tracking-wide uppercase">
                Ambient Intelligence System
              </span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              <span className="text-gradient-neural">Quorum</span>
              <br />
              <span className="text-foreground">Universe</span>
            </h1>
            
            <p className="text-xl text-muted-foreground mb-8 leading-relaxed max-w-2xl">
              A living network of 26 institutional archetypes arranged in hexagonal rings, 
              optimized for maximum synergy through ring-collapse algorithms. 
              Six philosopher minds validate truth through tribunal deliberation.
            </p>
            
            <div className="flex flex-wrap gap-4">
              <Link href="/archetypes">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-8 py-4 rounded-2xl bg-primary text-primary-foreground font-semibold 
                           shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 
                           transition-shadow"
                >
                  Explore Archetypes
                </motion.button>
              </Link>
              <Link href="/synergies">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-8 py-4 rounded-2xl border border-border bg-card/50 
                           hover:bg-card font-semibold transition-colors"
                >
                  View Hex-Ring Synergies
                </motion.button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 border-t border-border/50">
        <div className="container">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="neural-card p-6 text-center"
              >
                <stat.icon className={`w-8 h-8 mx-auto mb-3 ${stat.color}`} />
                <div className="text-3xl font-bold mb-1">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Links Section */}
      <section className="py-20">
        <div className="container">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Navigate the Neural Network
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Each node connects through optimized hexagonal ring topology.
              Explore the pathways below.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {quickLinks.map((link, index) => (
              <Link key={link.href} href={link.href}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                  whileHover={{ scale: 1.02, y: -4 }}
                  className="neural-card p-8 cursor-pointer group h-full"
                >
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${link.gradient} 
                                  flex items-center justify-center mb-6 
                                  group-hover:shadow-lg transition-shadow`}>
                    <link.icon className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold mb-3 group-hover:text-primary transition-colors">
                    {link.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {link.description}
                  </p>
                </motion.div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Philosopher Tribunal Preview */}
      <section className="py-20 relative overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-20"
          style={{ backgroundImage: "url('/images/philosopher-tribunal.png')" }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/90 to-background" />
        
        <div className="container relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
            >
              <div className="flex items-center gap-3 mb-4">
                <Cpu className="w-5 h-5 text-accent" />
                <span className="text-sm font-medium text-accent uppercase tracking-wide">
                  Truth Forensics Engine
                </span>
              </div>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">
                The Philosopher Tribunal
              </h2>
              <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
                Six philosophical minds deliberate on every claim. From Hume's empirical skepticism 
                to Zhuangzi's paradoxical wisdom, the tribunal chains perspectives to forge 
                consensus—or reveal irreducible complexity.
              </p>
              
              <div className="grid grid-cols-2 gap-4 mb-8">
                {[
                  { name: "Hume", style: "Empirical Skeptic", color: "philosopher-hume" },
                  { name: "Popper", style: "Falsificationist", color: "philosopher-popper" },
                  { name: "Quine", style: "Naturalist", color: "philosopher-quine" },
                  { name: "Arendt", style: "Political Theorist", color: "philosopher-arendt" },
                  { name: "Zhuangzi", style: "Daoist Sage", color: "philosopher-zhuangzi" },
                  { name: "Ibn Khaldun", style: "Civilizational Analyst", color: "philosopher-khaldun" },
                ].map((philosopher) => (
                  <div key={philosopher.name} className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${philosopher.color} bg-current`} />
                    <div>
                      <div className={`font-semibold ${philosopher.color}`}>{philosopher.name}</div>
                      <div className="text-xs text-muted-foreground">{philosopher.style}</div>
                    </div>
                  </div>
                ))}
              </div>
              
              <Link href="/tribunal">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-6 py-3 rounded-xl bg-accent text-accent-foreground font-semibold"
                >
                  Enter the Tribunal
                </motion.button>
              </Link>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 }}
              className="hidden lg:block"
            >
              <img 
                src="/images/philosopher-tribunal.png" 
                alt="Philosopher Tribunal Visualization"
                className="rounded-3xl shadow-2xl shadow-primary/10"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Hex-Ring Architecture */}
      <section className="py-20 border-t border-border/50">
        <div className="container">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Hexagonal Ring Topology
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Knowledge archetypes arranged in concentric hexagonal rings, optimized through 
              simulated annealing to maximize face-to-face synergy alignment.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { 
                title: "Ring Collapse", 
                tech: "Simulated Annealing",
                desc: "Rotate rings to minimize relational distance between adjacent disciplines",
                icon: Hexagon
              },
              { 
                title: "6-Face Alignment", 
                tech: "Theoretical • Empirical • Methodological",
                desc: "Each hex node has 6 relational faces scored against neighbors",
                icon: Network
              },
              { 
                title: "Synergy Bursts", 
                tech: "Cascade Detection",
                desc: "Identify high-synergy clusters that amplify knowledge transfer",
                icon: Zap
              },
            ].map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 + index * 0.1 }}
                className="neural-card p-6"
              >
                <item.icon className="w-10 h-10 text-primary mb-4" />
                <h3 className="text-xl font-bold mb-1">{item.title}</h3>
                <div className="text-sm text-primary mb-3">{item.tech}</div>
                <p className="text-muted-foreground text-sm">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </Layout>
  );
}
