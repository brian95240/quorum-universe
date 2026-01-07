import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import Layout from "@/components/Layout";
import {
  Zap,
  Target,
  TrendingUp,
  Shield,
  Cpu,
  Database,
  GitBranch,
  CheckCircle2,
} from "lucide-react";

interface ApexMetrics {
  synergy_score: number;
  cascade_potential: number;
  cache_efficiency: number;
  routing_accuracy: number;
  tribunal_consensus: number;
  resource_efficiency: number;
  total_apex_score: number;
}

interface Injection {
  id: string;
  category: string;
  target: string;
  impact_score: number;
  applied: boolean;
}

interface ApexResults {
  timestamp: string;
  duration_seconds: number;
  optimization_level: string;
  injections_applied: number;
  total_injections: number;
  metrics: ApexMetrics;
  injections: Injection[];
}

const metricIcons: Record<string, any> = {
  synergy_score: Zap,
  cascade_potential: TrendingUp,
  cache_efficiency: Database,
  routing_accuracy: GitBranch,
  tribunal_consensus: Shield,
  resource_efficiency: Cpu,
};

const metricLabels: Record<string, string> = {
  synergy_score: "Synergy Score",
  cascade_potential: "Cascade Potential",
  cache_efficiency: "Cache Efficiency",
  routing_accuracy: "Routing Accuracy",
  tribunal_consensus: "Tribunal Consensus",
  resource_efficiency: "Resource Efficiency",
};

const categoryColors: Record<string, string> = {
  intersection: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  cascade: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  routing: "bg-green-500/20 text-green-400 border-green-500/30",
  cache: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  tribunal: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  bridge: "bg-pink-500/20 text-pink-400 border-pink-500/30",
};

export default function Apex() {
  const [results, setResults] = useState<ApexResults | null>(null);

  useEffect(() => {
    fetch("/apex_optimization_results.json")
      .then((res) => res.json())
      .then((data) => setResults(data))
      .catch((err) => console.error("Failed to load apex results:", err));
  }, []);

  if (!results) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-cyan-400 animate-pulse">
            Loading apex optimization results...
          </div>
        </div>
      </Layout>
    );
  }

  const metrics = results.metrics;
  const metricKeys = Object.keys(metrics).filter(
    (k) => k !== "total_apex_score"
  ) as (keyof ApexMetrics)[];

  // Group injections by category
  const injectionsByCategory = results.injections.reduce((acc, inj) => {
    if (!acc[inj.category]) acc[inj.category] = [];
    acc[inj.category].push(inj);
    return acc;
  }, {} as Record<string, Injection[]>);

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <div className="flex items-center justify-center gap-3 mb-2">
            <Target className="w-10 h-10 text-cyan-400" />
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400">
              APEX VERTEX
            </h1>
          </div>
          <p className="text-cyan-200/60">
            All optimizations injected for maximum synergy extraction
          </p>
        </motion.div>

        {/* Total Apex Score */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-gradient-to-br from-cyan-900/30 to-teal-900/30 border-cyan-500/30">
            <CardContent className="p-8">
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="text-center md:text-left">
                  <div className="text-sm text-cyan-200/60 mb-1">
                    TOTAL APEX SCORE
                  </div>
                  <div className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400">
                    {(metrics.total_apex_score * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-cyan-200/60 mt-2">
                    {results.injections_applied}/{results.total_injections}{" "}
                    optimizations applied
                  </div>
                </div>

                <div className="flex-1 max-w-md">
                  <div className="relative h-4 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${metrics.total_apex_score * 100}%` }}
                      transition={{ duration: 1.5, ease: "easeOut" }}
                      className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-full"
                    />
                    <div
                      className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-400/50 to-emerald-400/50 rounded-full animate-pulse"
                      style={{ width: `${metrics.total_apex_score * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-cyan-200/40 mt-1">
                    <span>0%</span>
                    <span>Target: 92%</span>
                    <span>100%</span>
                  </div>
                </div>

                <div className="text-center">
                  <Badge
                    variant="outline"
                    className="text-lg px-4 py-2 border-cyan-500/50 text-cyan-400"
                  >
                    {results.optimization_level}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Individual Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {metricKeys.map((key, i) => {
            const Icon = metricIcons[key] || Zap;
            const value = metrics[key];
            return (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.05 }}
              >
                <Card className="bg-slate-900/50 border-cyan-500/20 h-full">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className="w-4 h-4 text-cyan-400" />
                      <span className="text-xs text-cyan-200/60 truncate">
                        {metricLabels[key]}
                      </span>
                    </div>
                    <div className="text-2xl font-bold text-cyan-300">
                      {(value * 100).toFixed(1)}%
                    </div>
                    <Progress
                      value={value * 100}
                      className="h-1 mt-2"
                    />
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {/* Cascade Potential Highlight */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 border-purple-500/30">
            <CardHeader>
              <CardTitle className="text-purple-400 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Cascade Amplification
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-4xl font-bold text-purple-300">
                    8,074.68x
                  </div>
                  <div className="text-sm text-purple-200/60">
                    Total cascade potential when all clusters activate
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-purple-200/60">
                    17 cascade steps
                  </div>
                  <div className="text-sm text-purple-200/60">
                    9 cross-domain bridges
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Injections by Category */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(injectionsByCategory).map(([category, injections], i) => (
            <motion.div
              key={category}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
            >
              <Card className="bg-slate-900/50 border-cyan-500/20 h-full">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center justify-between">
                    <span className="text-cyan-400 capitalize">{category}</span>
                    <Badge
                      variant="outline"
                      className={categoryColors[category] || "border-cyan-500/30"}
                    >
                      {injections.length}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 max-h-48 overflow-y-auto">
                  {injections.slice(0, 5).map((inj) => (
                    <div
                      key={inj.id}
                      className="flex items-center justify-between p-2 rounded bg-slate-800/30"
                    >
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-400" />
                        <span className="text-sm text-cyan-200/80 truncate max-w-[150px]">
                          {inj.target.replace(/_/g, " ")}
                        </span>
                      </div>
                      <span className="text-xs text-cyan-400">
                        +{(inj.impact_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                  {injections.length > 5 && (
                    <div className="text-xs text-cyan-200/40 text-center">
                      +{injections.length - 5} more
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Optimization Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <Card className="bg-slate-900/50 border-cyan-500/20">
            <CardHeader>
              <CardTitle className="text-cyan-400">
                Apex Optimization Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                <div className="p-3 rounded bg-slate-800/30">
                  <div className="text-cyan-200/60">Hex-Ring Rotations</div>
                  <div className="text-cyan-300 font-medium">
                    4 rings optimized
                  </div>
                </div>
                <div className="p-3 rounded bg-slate-800/30">
                  <div className="text-cyan-200/60">Intersection Weights</div>
                  <div className="text-cyan-300 font-medium">
                    17 weights tuned
                  </div>
                </div>
                <div className="p-3 rounded bg-slate-800/30">
                  <div className="text-cyan-200/60">Routing Table</div>
                  <div className="text-cyan-300 font-medium">
                    26 archetypes mapped
                  </div>
                </div>
                <div className="p-3 rounded bg-slate-800/30">
                  <div className="text-cyan-200/60">Tribunal Rules</div>
                  <div className="text-cyan-300 font-medium">
                    6 philosophers active
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </Layout>
  );
}
