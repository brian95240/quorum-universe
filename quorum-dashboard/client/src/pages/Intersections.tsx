import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import Layout from "@/components/Layout";

interface Intersection {
  id: string;
  type: string;
  source_module: string;
  target_module: string;
  weight: number;
  synergy_potential: number;
}

interface HiddenCluster {
  id: string;
  name: string;
  intersections: string[];
  total_synergy: number;
  activation_energy: number;
  cascade_multiplier: number;
  discovery_method: string;
  properties: Record<string, any>;
}

interface Recommendation {
  id: string;
  priority: string;
  title: string;
  description: string;
  affected_intersections: string[];
  actions: string[];
}

interface AnnealingReport {
  timestamp: string;
  duration_seconds: number;
  annealing: {
    iterations: number;
    improvements: number;
    best_energy: number;
  };
  intersections: Intersection[];
  hidden_clusters: HiddenCluster[];
  cascade_analysis: {
    total_cascade_potential: number;
    activated_clusters: number;
    activation_sequence: Array<{
      cluster_id: string;
      cluster_name: string;
      activation_energy: number;
      cascade_multiplier: number;
      resulting_energy: number;
    }>;
  };
  recommendations: Recommendation[];
  summary: {
    total_intersections: number;
    total_hidden_clusters: number;
    best_annealing_energy: number;
    total_cascade_potential: number;
  };
}

export default function Intersections() {
  const [report, setReport] = useState<AnnealingReport | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<HiddenCluster | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetch("/intersection_annealing_report.json")
      .then((res) => res.json())
      .then((data) => setReport(data))
      .catch((err) => console.error("Failed to load report:", err));
  }, []);

  useEffect(() => {
    if (!report || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth * 2;
    canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);

    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;

    // Animation frame
    let animationId: number;
    let time = 0;

    const modules = [
      { id: "config", x: width * 0.5, y: height * 0.15 },
      { id: "hex_ring_optimizer", x: width * 0.25, y: height * 0.35 },
      { id: "graph_engine", x: width * 0.75, y: height * 0.35 },
      { id: "synergy_analyzer", x: width * 0.2, y: height * 0.6 },
      { id: "redis_cache_manager", x: width * 0.5, y: height * 0.55 },
      { id: "api_server", x: width * 0.8, y: height * 0.6 },
      { id: "symbiotic_connector", x: width * 0.5, y: height * 0.85 },
    ];

    const moduleMap = new Map(modules.map((m) => [m.id, m]));

    const draw = () => {
      ctx.fillStyle = "#0d1f22";
      ctx.fillRect(0, 0, width, height);

      // Draw connections (intersections)
      report.intersections.forEach((intersection) => {
        const source = moduleMap.get(intersection.source_module);
        const target = moduleMap.get(intersection.target_module);
        if (!source || !target) return;

        const synergy = intersection.synergy_potential;
        const pulseIntensity = 0.5 + 0.5 * Math.sin(time * 0.02 + synergy * 10);

        // Draw connection line
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);

        const gradient = ctx.createLinearGradient(
          source.x,
          source.y,
          target.x,
          target.y
        );
        gradient.addColorStop(0, `rgba(0, 255, 213, ${synergy * pulseIntensity})`);
        gradient.addColorStop(0.5, `rgba(0, 200, 255, ${synergy * pulseIntensity})`);
        gradient.addColorStop(1, `rgba(0, 255, 213, ${synergy * pulseIntensity})`);

        ctx.strokeStyle = gradient;
        ctx.lineWidth = 1 + synergy * 3;
        ctx.stroke();

        // Draw energy particles along the line
        const particleCount = Math.floor(synergy * 5);
        for (let i = 0; i < particleCount; i++) {
          const t = ((time * 0.005 + i / particleCount) % 1);
          const px = source.x + (target.x - source.x) * t;
          const py = source.y + (target.y - source.y) * t;

          ctx.beginPath();
          ctx.arc(px, py, 2 + synergy * 2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(0, 255, 213, ${pulseIntensity})`;
          ctx.fill();
        }
      });

      // Draw module nodes
      modules.forEach((module) => {
        const isHub = report.hidden_clusters.some(
          (c) => c.id === `hub_${module.id}`
        );
        const nodeSize = isHub ? 35 : 25;
        const pulseSize = nodeSize + 5 * Math.sin(time * 0.03);

        // Glow effect
        const gradient = ctx.createRadialGradient(
          module.x,
          module.y,
          0,
          module.x,
          module.y,
          pulseSize * 2
        );
        gradient.addColorStop(0, "rgba(0, 255, 213, 0.8)");
        gradient.addColorStop(0.5, "rgba(0, 255, 213, 0.2)");
        gradient.addColorStop(1, "rgba(0, 255, 213, 0)");

        ctx.beginPath();
        ctx.arc(module.x, module.y, pulseSize * 2, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();

        // Node circle
        ctx.beginPath();
        ctx.arc(module.x, module.y, pulseSize, 0, Math.PI * 2);
        ctx.fillStyle = isHub ? "#00ffd5" : "#0d3d3d";
        ctx.fill();
        ctx.strokeStyle = "#00ffd5";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Module label
        ctx.fillStyle = "#e0f7f7";
        ctx.font = "11px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(
          module.id.replace(/_/g, " "),
          module.x,
          module.y + pulseSize + 15
        );
      });

      // Draw cascade energy indicator
      const cascadeEnergy = report.cascade_analysis.total_cascade_potential;
      ctx.fillStyle = "#00ffd5";
      ctx.font = "bold 14px Outfit, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(`Cascade Potential: ${cascadeEnergy.toFixed(0)}x`, 20, 30);

      time++;
      animationId = requestAnimationFrame(draw);
    };

    draw();

    return () => cancelAnimationFrame(animationId);
  }, [report]);

  if (!report) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-cyan-400 animate-pulse">
            Loading intersection analysis...
          </div>
        </div>
      </Layout>
    );
  }

  const priorityColors: Record<string, string> = {
    high: "bg-red-500/20 text-red-400 border-red-500/30",
    medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    low: "bg-green-500/20 text-green-400 border-green-500/30",
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-teal-300 mb-2">
            Intersection Annealing
          </h1>
          <p className="text-cyan-200/60">
            Hidden synergy networks discovered through simulated annealing at
            code intersections
          </p>
        </motion.div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            {
              label: "Intersections",
              value: report.summary.total_intersections,
            },
            {
              label: "Hidden Clusters",
              value: report.summary.total_hidden_clusters,
            },
            {
              label: "Annealing Energy",
              value: report.summary.best_annealing_energy.toFixed(4),
            },
            {
              label: "Cascade Potential",
              value: `${report.summary.total_cascade_potential.toFixed(0)}x`,
            },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card className="bg-slate-900/50 border-cyan-500/20">
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-cyan-400">
                    {stat.value}
                  </div>
                  <div className="text-sm text-cyan-200/60">{stat.label}</div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Intersection Network Visualization */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-slate-900/50 border-cyan-500/20">
            <CardHeader>
              <CardTitle className="text-cyan-400">
                Intersection Network
              </CardTitle>
            </CardHeader>
            <CardContent>
              <canvas
                ref={canvasRef}
                className="w-full h-[400px] rounded-lg"
                style={{ background: "#0d1f22" }}
              />
            </CardContent>
          </Card>
        </motion.div>

        {/* Hidden Clusters */}
        <div className="grid md:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="bg-slate-900/50 border-cyan-500/20 h-full">
              <CardHeader>
                <CardTitle className="text-cyan-400">
                  Hidden Synergy Clusters
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 max-h-[400px] overflow-y-auto">
                {report.hidden_clusters.slice(0, 10).map((cluster, i) => (
                  <motion.div
                    key={cluster.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + i * 0.05 }}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedCluster?.id === cluster.id
                        ? "bg-cyan-500/20 border-cyan-400"
                        : "bg-slate-800/50 border-slate-700/50 hover:border-cyan-500/50"
                    }`}
                    onClick={() => setSelectedCluster(cluster)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium text-cyan-300">
                        {cluster.name}
                      </span>
                      <Badge
                        variant="outline"
                        className="text-xs border-cyan-500/30 text-cyan-400"
                      >
                        {cluster.cascade_multiplier.toFixed(2)}x
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-cyan-200/60">Synergy:</span>
                      <Progress
                        value={(cluster.total_synergy / 10) * 100}
                        className="flex-1 h-2"
                      />
                      <span className="text-cyan-400">
                        {cluster.total_synergy.toFixed(2)}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Cascade Activation Sequence */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="bg-slate-900/50 border-cyan-500/20 h-full">
              <CardHeader>
                <CardTitle className="text-cyan-400">
                  Cascade Activation Sequence
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 max-h-[400px] overflow-y-auto">
                {report.cascade_analysis.activation_sequence
                  .slice(0, 10)
                  .map((step, i) => (
                    <motion.div
                      key={step.cluster_id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.6 + i * 0.05 }}
                      className="flex items-center gap-3 p-2 rounded bg-slate-800/30"
                    >
                      <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center text-xs text-cyan-400">
                        {i + 1}
                      </div>
                      <div className="flex-1">
                        <div className="text-sm text-cyan-300">
                          {step.cluster_name}
                        </div>
                        <div className="text-xs text-cyan-200/50">
                          Energy: {step.activation_energy.toFixed(3)} →{" "}
                          {step.resulting_energy.toFixed(1)}x
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className="text-xs border-cyan-500/30"
                      >
                        ×{step.cascade_multiplier.toFixed(2)}
                      </Badge>
                    </motion.div>
                  ))}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Recommendations */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="bg-slate-900/50 border-cyan-500/20">
            <CardHeader>
              <CardTitle className="text-cyan-400">
                Optimization Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {report.recommendations.map((rec, i) => (
                <motion.div
                  key={rec.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + i * 0.1 }}
                  className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50"
                >
                  <div className="flex items-start gap-3 mb-2">
                    <Badge
                      variant="outline"
                      className={priorityColors[rec.priority]}
                    >
                      {rec.priority.toUpperCase()}
                    </Badge>
                    <div>
                      <h4 className="font-medium text-cyan-300">{rec.title}</h4>
                      <p className="text-sm text-cyan-200/60 mt-1">
                        {rec.description}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 pl-4 border-l-2 border-cyan-500/30">
                    <div className="text-xs text-cyan-200/50 mb-1">Actions:</div>
                    <ul className="text-sm text-cyan-200/80 space-y-1">
                      {rec.actions.map((action, j) => (
                        <li key={j} className="flex items-center gap-2">
                          <span className="w-1 h-1 rounded-full bg-cyan-400" />
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </Layout>
  );
}
