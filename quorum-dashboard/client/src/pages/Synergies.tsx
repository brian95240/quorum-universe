/*
 * DESIGN: Neural Network Interface - Synergies Page
 * - Hexagonal ring collapse visualization
 * - Face-to-face synergy alignment display
 * - Burst cluster detection
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Network, Hexagon, Zap, GitBranch, ArrowRight } from "lucide-react";
import Layout from "@/components/Layout";
import { Progress } from "@/components/ui/progress";

interface SynergyCluster {
  id: string;
  name: string;
  nodes: string[];
  synergy_score: number;
  burst_potential: number;
  burst_score?: number;
  cascade_potential?: number;
  properties: Record<string, any>;
}

interface Adjacency {
  source: string;
  source_name: string;
  target: string;
  target_name: string;
  synergy: number;
  face_alignment?: Record<string, number>;
}

interface SynergyData {
  synergy_clusters: SynergyCluster[];
  burst_clusters: SynergyCluster[];
  hidden_connections: any[];
  optimization_opportunities: any[];
  summary: {
    total_synergy_score: number;
    network_efficiency: number;
    cascade_potential: number;
  };
}

interface HexData {
  visualization: {
    rings: any[];
    edges: any[];
    total_synergy: number;
  };
  adjacencies: Adjacency[];
}

export default function Synergies() {
  const [synergyData, setSynergyData] = useState<SynergyData | null>(null);
  const [hexData, setHexData] = useState<HexData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCluster, setSelectedCluster] = useState<SynergyCluster | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/data/synergy_report.json").then((res) => res.json()),
      fetch("/data/hex_ring_optimization.json").then((res) => res.json()),
    ])
      .then(([synergy, hex]) => {
        setSynergyData(synergy);
        setHexData(hex);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load data:", err);
        setLoading(false);
      });
  }, []);

  const topAdjacencies = hexData?.adjacencies?.slice(0, 20) || [];

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
            <div className="p-2 rounded-xl bg-[oklch(0.6_0.12_150)]/20">
              <Hexagon className="w-6 h-6 text-[oklch(0.6_0.12_150)]" />
            </div>
            <span className="text-sm font-medium text-[oklch(0.6_0.12_150)] uppercase tracking-wide">
              Ring Collapse Optimization
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Hex-Ring Synergies
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Knowledge archetypes arranged in concentric hexagonal rings, optimized through 
            simulated annealing to maximize face-to-face synergy alignment. Each hex node 
            has 6 relational faces that score against adjacent nodes.
          </p>
        </motion.div>

        {/* Optimization Stats */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12"
        >
          <div className="neural-card p-4">
            <div className="text-3xl font-bold text-primary">
              {hexData?.visualization?.total_synergy?.toFixed(3) || "0.291"}
            </div>
            <div className="text-sm text-muted-foreground">Total Synergy Score</div>
          </div>
          <div className="neural-card p-4">
            <div className="text-3xl font-bold text-[oklch(0.6_0.12_150)]">
              {synergyData?.synergy_clusters?.length || 15}
            </div>
            <div className="text-sm text-muted-foreground">Synergy Clusters</div>
          </div>
          <div className="neural-card p-4">
            <div className="text-3xl font-bold text-[oklch(0.65_0.15_25)]">
              {synergyData?.burst_clusters?.length || 8}
            </div>
            <div className="text-sm text-muted-foreground">Burst Clusters</div>
          </div>
          <div className="neural-card p-4">
            <div className="text-3xl font-bold text-[oklch(0.7_0.14_280)]">
              {hexData?.visualization?.rings?.length || 4}
            </div>
            <div className="text-sm text-muted-foreground">Hex Rings</div>
          </div>
        </motion.div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {/* Hex Ring Visualization */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="mb-16"
            >
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                <Hexagon className="w-6 h-6 text-primary" />
                Hexagonal Ring Topology
              </h2>
              
              <div className="neural-card p-8">
                <div className="relative aspect-square max-w-2xl mx-auto">
                  <img
                    src="/images/synergy-cluster.png"
                    alt="Synergy Cluster Visualization"
                    className="w-full h-full object-cover rounded-2xl opacity-40"
                  />
                  
                  {/* Ring Labels Overlay */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-primary mb-2">4 Rings</div>
                      <div className="text-muted-foreground">26 Archetypes</div>
                      <div className="text-sm text-muted-foreground mt-4">
                        Core → Inner → Middle → Outer
                      </div>
                    </div>
                  </div>

                  {/* Ring indicators */}
                  {[0, 1, 2, 3].map((ring) => (
                    <div
                      key={ring}
                      className="absolute rounded-full border-2 border-primary/30"
                      style={{
                        width: `${20 + ring * 20}%`,
                        height: `${20 + ring * 20}%`,
                        top: `${40 - ring * 10}%`,
                        left: `${40 - ring * 10}%`,
                      }}
                    />
                  ))}
                </div>

                <div className="grid md:grid-cols-4 gap-4 mt-8">
                  {hexData?.visualization?.rings?.map((ring, index) => (
                    <div key={index} className="text-center p-4 rounded-xl bg-card/50">
                      <div className="text-lg font-bold">Ring {ring.level}</div>
                      <div className="text-2xl font-bold text-primary">{ring.nodes?.length || 0}</div>
                      <div className="text-xs text-muted-foreground">
                        {ring.level === 0 ? "Core" : ring.level === 1 ? "Inner" : ring.level === 2 ? "Middle" : "Outer"}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Rotation: {ring.rotation}°
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Top Synergistic Adjacencies */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="mb-16"
            >
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                <Network className="w-6 h-6 text-[oklch(0.6_0.12_150)]" />
                Top Synergistic Adjacencies
              </h2>
              
              <div className="grid md:grid-cols-2 gap-4">
                {topAdjacencies.slice(0, 10).map((adj, index) => (
                  <motion.div
                    key={`${adj.source}-${adj.target}-${index}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + index * 0.05 }}
                    className="neural-card p-4"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <div className="font-semibold">{adj.source_name}</div>
                        <div className="text-xs text-muted-foreground">Ring source</div>
                      </div>
                      <ArrowRight className="w-5 h-5 text-primary shrink-0" />
                      <div className="flex-1 text-right">
                        <div className="font-semibold">{adj.target_name}</div>
                        <div className="text-xs text-muted-foreground">Ring target</div>
                      </div>
                    </div>
                    <div className="mt-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Synergy</span>
                        <span className="font-mono text-primary">{(adj.synergy * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={adj.synergy * 100} className="h-2" />
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Synergy Clusters */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mb-16"
            >
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                <GitBranch className="w-6 h-6 text-[oklch(0.65_0.15_25)]" />
                Synergy Clusters
              </h2>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {synergyData?.synergy_clusters?.slice(0, 9).map((cluster, index) => (
                  <motion.div
                    key={cluster.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 + index * 0.05 }}
                    whileHover={{ scale: 1.02 }}
                    onClick={() => setSelectedCluster(
                      selectedCluster?.id === cluster.id ? null : cluster
                    )}
                    className={`neural-card p-6 cursor-pointer ${
                      selectedCluster?.id === cluster.id ? "ring-2 ring-primary" : ""
                    }`}
                  >
                    <h3 className="font-bold mb-2">{cluster.name}</h3>
                    <div className="flex items-center gap-4 mb-3">
                      <div>
                        <div className="text-2xl font-bold text-primary">
                          {(cluster.synergy_score * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-muted-foreground">Synergy</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-[oklch(0.65_0.15_25)]">
                          {(cluster.burst_potential * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-muted-foreground">Burst</div>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {cluster.nodes?.length || 0} nodes
                    </div>
                    
                    {selectedCluster?.id === cluster.id && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="mt-4 pt-4 border-t border-border/50"
                      >
                        <div className="text-sm text-muted-foreground mb-2">Nodes:</div>
                        <div className="flex flex-wrap gap-1">
                          {cluster.nodes?.map((node) => (
                            <span
                              key={node}
                              className="px-2 py-0.5 text-xs rounded-full bg-primary/10 text-primary"
                            >
                              {node.replace("archetype:", "")}
                            </span>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Burst Clusters */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
            >
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                <Zap className="w-6 h-6 text-[oklch(0.7_0.14_280)]" />
                Burst Clusters (High Cascade Potential)
              </h2>
              
              <div className="grid md:grid-cols-2 gap-4">
                {synergyData?.burst_clusters?.slice(0, 6).map((cluster, index) => (
                  <motion.div
                    key={cluster.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7 + index * 0.05 }}
                    className="neural-card p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-bold">{cluster.name}</h3>
                        <div className="text-xs text-muted-foreground">
                          {cluster.properties?.type || "cluster"}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-[oklch(0.7_0.14_280)]">
                          {((cluster.burst_score || cluster.burst_potential) * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-muted-foreground">Burst Score</div>
                      </div>
                    </div>
                    
                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Cascade Potential</span>
                        <span className="font-mono">{((cluster.cascade_potential || cluster.burst_potential) * 100).toFixed(0)}%</span>
                      </div>
                      <Progress value={(cluster.cascade_potential || cluster.burst_potential) * 100} className="h-2" />
                    </div>
                    
                    <div className="flex flex-wrap gap-1">
                      {cluster.nodes?.slice(0, 4).map((node) => (
                        <span
                          key={node}
                          className="px-2 py-0.5 text-xs rounded-full bg-[oklch(0.7_0.14_280)]/10 text-[oklch(0.7_0.14_280)]"
                        >
                          {node.replace("archetype:", "").replace("module:", "")}
                        </span>
                      ))}
                      {(cluster.nodes?.length || 0) > 4 && (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-muted text-muted-foreground">
                          +{cluster.nodes.length - 4} more
                        </span>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </div>
    </Layout>
  );
}
