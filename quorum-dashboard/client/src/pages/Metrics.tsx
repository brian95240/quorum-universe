/*
 * DESIGN: Neural Network Interface - Metrics Page
 * - Real-time system monitoring visualization
 * - Cache efficiency metrics
 * - Network health indicators
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Activity, 
  Cpu, 
  Database, 
  Zap, 
  Clock, 
  HardDrive,
  Network,
  MemoryStick,
  CheckCircle,
  AlertCircle
} from "lucide-react";
import Layout from "@/components/Layout";
import { Progress } from "@/components/ui/progress";

interface SystemMetric {
  label: string;
  value: number;
  max: number;
  unit: string;
  status: "healthy" | "warning" | "critical";
}

interface CacheMetric {
  tier: string;
  hitRate: number;
  size: string;
  compression: string;
}

const mockSystemMetrics: SystemMetric[] = [
  { label: "CPU Usage", value: 23, max: 100, unit: "%", status: "healthy" },
  { label: "Memory", value: 4.2, max: 16, unit: "GB", status: "healthy" },
  { label: "Disk I/O", value: 156, max: 500, unit: "MB/s", status: "healthy" },
  { label: "Network", value: 89, max: 1000, unit: "Mbps", status: "healthy" },
];

const mockCacheMetrics: CacheMetric[] = [
  { tier: "L1 (Hot)", hitRate: 94.2, size: "256 MB", compression: "None" },
  { tier: "L2 (Warm)", hitRate: 87.5, size: "2 GB", compression: "Zstd" },
  { tier: "L3 (Cold)", hitRate: 72.3, size: "16 GB", compression: "Zstd-19" },
];

const stackComponents = [
  { name: "Apache AGE", status: "operational", latency: "2.3ms" },
  { name: "PostgreSQL 17", status: "operational", latency: "1.8ms" },
  { name: "NetworkX", status: "operational", latency: "0.5ms" },
  { name: "Redis L1/L2", status: "operational", latency: "0.1ms" },
  { name: "Neon DB", status: "operational", latency: "12ms" },
  { name: "MADlib", status: "operational", latency: "3.2ms" },
];

export default function Metrics() {
  const [metrics, setMetrics] = useState(mockSystemMetrics);
  const [uptime, setUptime] = useState(0);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics((prev) =>
        prev.map((m) => ({
          ...m,
          value: Math.max(0, Math.min(m.max, m.value + (Math.random() - 0.5) * 5)),
        }))
      );
      setUptime((prev) => prev + 1);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${mins}m`;
  };

  return (
    <Layout>
      <div className="container py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-xl bg-[oklch(0.7_0.14_280)]/20">
              <Activity className="w-6 h-6 text-[oklch(0.7_0.14_280)]" />
            </div>
            <span className="text-sm font-medium text-[oklch(0.7_0.14_280)] uppercase tracking-wide">
              System Monitoring
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            System Metrics
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Real-time performance monitoring for the Quorum Universe FOSS stack.
            Apache AGE, NetworkX, PostgreSQL, and Redis working in harmony.
          </p>
        </motion.div>

        {/* Status Overview */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12"
        >
          <div className="neural-card p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/20">
              <CheckCircle className="w-6 h-6 text-green-500" />
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Status</div>
              <div className="font-bold text-green-500">Operational</div>
            </div>
          </div>
          <div className="neural-card p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/20">
              <Clock className="w-6 h-6 text-primary" />
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Uptime</div>
              <div className="font-bold">{formatUptime(uptime + 259200)}</div>
            </div>
          </div>
          <div className="neural-card p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[oklch(0.6_0.12_150)]/20">
              <Database className="w-6 h-6 text-[oklch(0.6_0.12_150)]" />
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Corpus</div>
              <div className="font-bold">846 GB</div>
            </div>
          </div>
          <div className="neural-card p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[oklch(0.65_0.15_25)]/20">
              <Zap className="w-6 h-6 text-[oklch(0.65_0.15_25)]" />
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Queries/s</div>
              <div className="font-bold">1,247</div>
            </div>
          </div>
        </motion.div>

        {/* System Resources */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mb-12"
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <Cpu className="w-6 h-6 text-primary" />
            System Resources
          </h2>
          
          <div className="grid md:grid-cols-2 gap-4">
            {metrics.map((metric, index) => (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                className="neural-card p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {metric.label === "CPU Usage" && <Cpu className="w-5 h-5 text-primary" />}
                    {metric.label === "Memory" && <MemoryStick className="w-5 h-5 text-[oklch(0.6_0.12_150)]" />}
                    {metric.label === "Disk I/O" && <HardDrive className="w-5 h-5 text-[oklch(0.65_0.15_25)]" />}
                    {metric.label === "Network" && <Network className="w-5 h-5 text-[oklch(0.7_0.14_280)]" />}
                    <span className="font-semibold">{metric.label}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-bold">{metric.value.toFixed(1)}</span>
                    <span className="text-muted-foreground ml-1">{metric.unit}</span>
                  </div>
                </div>
                <Progress 
                  value={(metric.value / metric.max) * 100} 
                  className="h-3"
                />
                <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                  <span>0 {metric.unit}</span>
                  <span>{metric.max} {metric.unit}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Cache Performance */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mb-12"
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <Zap className="w-6 h-6 text-[oklch(0.65_0.15_25)]" />
            Multi-Tier Cache Performance
          </h2>
          
          <div className="grid md:grid-cols-3 gap-4">
            {mockCacheMetrics.map((cache, index) => (
              <motion.div
                key={cache.tier}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className="neural-card p-6"
              >
                <div className="text-lg font-bold mb-4">{cache.tier}</div>
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Hit Rate</span>
                    <span className="font-mono text-primary">{cache.hitRate}%</span>
                  </div>
                  <Progress value={cache.hitRate} className="h-2" />
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Size</div>
                    <div className="font-semibold">{cache.size}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Compression</div>
                    <div className="font-semibold">{cache.compression}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Stack Components */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <Database className="w-6 h-6 text-[oklch(0.6_0.12_150)]" />
            FOSS Stack Components
          </h2>
          
          <div className="neural-card overflow-hidden">
            <div className="grid grid-cols-3 gap-4 p-4 bg-card/50 border-b border-border/50 text-sm font-semibold text-muted-foreground">
              <div>Component</div>
              <div>Status</div>
              <div>Latency</div>
            </div>
            
            {stackComponents.map((component, index) => (
              <motion.div
                key={component.name}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 + index * 0.05 }}
                className="grid grid-cols-3 gap-4 p-4 border-b border-border/30 last:border-0"
              >
                <div className="font-semibold">{component.name}</div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="text-green-500 capitalize">{component.status}</span>
                </div>
                <div className="font-mono text-muted-foreground">{component.latency}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Architecture Diagram */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="mt-12"
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <Network className="w-6 h-6 text-primary" />
            System Architecture
          </h2>
          
          <div className="neural-card p-8">
            <img
              src="/images/data-flow-pattern.png"
              alt="System Architecture"
              className="w-full max-w-3xl mx-auto rounded-2xl opacity-80"
            />
            
            <div className="grid md:grid-cols-3 gap-6 mt-8">
              <div className="text-center">
                <div className="text-3xl font-bold text-primary">70%</div>
                <div className="text-sm text-muted-foreground">Storage Reduction</div>
                <div className="text-xs text-muted-foreground mt-1">via Zstandard compression</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-[oklch(0.6_0.12_150)]">3x</div>
                <div className="text-sm text-muted-foreground">Query Speedup</div>
                <div className="text-xs text-muted-foreground mt-1">vs Neo4j Enterprise</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-[oklch(0.65_0.15_25)]">100%</div>
                <div className="text-sm text-muted-foreground">FOSS Stack</div>
                <div className="text-xs text-muted-foreground mt-1">No proprietary dependencies</div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
}
