/*
 * DESIGN: Neural Network Interface - Biopunk/Organic Tech
 * - Dendrite-like navigation branches
 * - Organic flowing sidebar
 * - Breathing ambient background
 */

import { Link, useLocation } from "wouter";
import { motion } from "framer-motion";
import { 
  Brain, 
  Network, 
  Users, 
  Activity, 
  Home,
  Menu,
  X,
  Hexagon,
  GitBranch,
  Target
} from "lucide-react";
import { useState } from "react";

interface LayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/archetypes", label: "Archetypes", icon: Brain },
  { href: "/tribunal", label: "Tribunal", icon: Users },
  { href: "/synergies", label: "Synergies", icon: Network },
  { href: "/intersections", label: "Intersections", icon: GitBranch },
  { href: "/apex", label: "Apex", icon: Target },
  { href: "/metrics", label: "Metrics", icon: Activity },
];

export default function Layout({ children }: LayoutProps) {
  const [location] = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Background Pattern */}
      <div 
        className="fixed inset-0 opacity-5 pointer-events-none"
        style={{ 
          backgroundImage: "url('/images/data-flow-pattern.png')",
          backgroundSize: "cover",
        }}
      />
      
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="container flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/">
            <motion.div 
              className="flex items-center gap-3 cursor-pointer"
              whileHover={{ scale: 1.02 }}
            >
              <div className="relative">
                <Hexagon className="w-9 h-9 text-primary" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-3 h-3 rounded-full bg-primary animate-pulse" />
                </div>
              </div>
              <div>
                <span className="text-lg font-bold text-gradient-neural">Quorum</span>
                <span className="text-lg font-bold text-foreground ml-1">Universe</span>
              </div>
            </motion.div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = location === item.href;
              return (
                <Link key={item.href} href={item.href}>
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`
                      flex items-center gap-2 px-4 py-2 rounded-xl cursor-pointer
                      transition-colors duration-200
                      ${isActive 
                        ? 'bg-primary/20 text-primary' 
                        : 'text-muted-foreground hover:text-foreground hover:bg-card/50'
                      }
                    `}
                  >
                    <item.icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </motion.div>
                </Link>
              );
            })}
          </nav>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-card/50"
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <motion.nav
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="md:hidden border-t border-border/50 bg-background/95 backdrop-blur-xl"
          >
            <div className="container py-4 space-y-2">
              {navItems.map((item) => {
                const isActive = location === item.href;
                return (
                  <Link key={item.href} href={item.href}>
                    <div
                      onClick={() => setMobileMenuOpen(false)}
                      className={`
                        flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer
                        ${isActive 
                          ? 'bg-primary/20 text-primary' 
                          : 'text-muted-foreground hover:text-foreground hover:bg-card/50'
                        }
                      `}
                    >
                      <item.icon className="w-5 h-5" />
                      <span className="font-medium">{item.label}</span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </motion.nav>
        )}
      </header>

      {/* Main Content */}
      <main className="pt-16 min-h-screen">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 py-8 mt-20">
        <div className="container">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Hexagon className="w-5 h-5 text-primary" />
              <span className="text-sm">Quorum Universe v3.0</span>
            </div>
            <div className="text-sm text-muted-foreground">
              FOSS-First Ambient Intelligence • Apache AGE • NetworkX • PostgreSQL
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
