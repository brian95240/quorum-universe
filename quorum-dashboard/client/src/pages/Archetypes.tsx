/*
 * DESIGN: Neural Network Interface - Archetypes Page
 * - Hexagonal ring visualization of 26 archetypes
 * - Face affinity details on hover
 * - Cluster grouping with organic styling
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Brain, Hexagon, Database, BookOpen, Search } from "lucide-react";
import Layout from "@/components/Layout";
import { Input } from "@/components/ui/input";

interface ArchetypeNode {
  id: string;
  name: string;
  cluster: string;
  domains: string[];
  corpus_size_gb: number;
  position: number;
  angle: number;
  face_affinities: Record<string, number>;
}

interface RingData {
  level: number;
  size: number;
  rotation: number;
  nodes: ArchetypeNode[];
}

interface HexData {
  rings: RingData[];
  edges: Array<{ source: string; target: string; synergy: number }>;
  total_synergy: number;
}

const clusterColors: Record<string, string> = {
  meta_cognitive: "from-[oklch(0.7_0.14_280)] to-[oklch(0.6_0.12_280)]",
  stem_core: "from-[oklch(0.75_0.18_195)] to-[oklch(0.6_0.15_195)]",
  life_systems: "from-[oklch(0.7_0.18_150)] to-[oklch(0.55_0.15_150)]",
  applied_tech: "from-[oklch(0.7_0.15_55)] to-[oklch(0.55_0.12_55)]",
  human_systems: "from-[oklch(0.65_0.15_25)] to-[oklch(0.5_0.12_25)]",
  non_western: "from-[oklch(0.7_0.12_85)] to-[oklch(0.55_0.1_85)]",
  creative_synthesis: "from-[oklch(0.65_0.18_320)] to-[oklch(0.5_0.15_320)]",
};

const clusterLabels: Record<string, string> = {
  meta_cognitive: "Meta-Cognitive",
  stem_core: "STEM Core",
  life_systems: "Life Systems",
  applied_tech: "Applied Tech",
  human_systems: "Human Systems",
  non_western: "Non-Western",
  creative_synthesis: "Creative Synthesis",
};

export default function Archetypes() {
  const [hexData, setHexData] = useState<HexData | null>(null);
  const [selectedArchetype, setSelectedArchetype] = useState<ArchetypeNode | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/data/hex_ring_optimization.json")
      .then((res) => res.json())
      .then((data) => {
        setHexData(data.visualization);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load hex data:", err);
        setLoading(false);
      });
  }, []);

  const allNodes = hexData?.rings.flatMap((ring) => ring.nodes) || [];
  
  const filteredNodes = allNodes.filter((node) =>
    node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    node.cluster.toLowerCase().includes(searchQuery.toLowerCase()) ||
    node.domains.some((d) => d.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const groupedByCluster = filteredNodes.reduce((acc, node) => {
    if (!acc[node.cluster]) acc[node.cluster] = [];
    acc[node.cluster].push(node);
    return acc;
  }, {} as Record<string, ArchetypeNode[]>);

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
            <div className="p-2 rounded-xl bg-primary/20">
              <Brain className="w-6 h-6 text-primary" />
            </div>
            <span className="text-sm font-medium text-primary uppercase tracking-wide">
              Knowledge Network
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            26 Institutional Archetypes
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Arranged in hexagonal rings with optimized face-to-face synergy alignment.
            Each archetype has 6 relational faces: Theoretical, Empirical, Methodological,
            Historical, Applied, and Philosophical.
          </p>
        </motion.div>

        {/* Search */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              placeholder="Search archetypes, clusters, or domains..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-card/50 border-border/50"
            />
          </div>
        </motion.div>

        {/* Stats Bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12"
        >
          <div className="neural-card p-4 flex items-center gap-3">
            <Hexagon className="w-8 h-8 text-primary" />
            <div>
              <div className="text-2xl font-bold">{allNodes.length}</div>
              <div className="text-xs text-muted-foreground">Archetypes</div>
            </div>
          </div>
          <div className="neural-card p-4 flex items-center gap-3">
            <Database className="w-8 h-8 text-[oklch(0.6_0.12_150)]" />
            <div>
              <div className="text-2xl font-bold">846 GB</div>
              <div className="text-xs text-muted-foreground">Total Corpus</div>
            </div>
          </div>
          <div className="neural-card p-4 flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-[oklch(0.65_0.15_25)]" />
            <div>
              <div className="text-2xl font-bold">{hexData?.rings.length || 4}</div>
              <div className="text-xs text-muted-foreground">Hex Rings</div>
            </div>
          </div>
          <div className="neural-card p-4 flex items-center gap-3">
            <Brain className="w-8 h-8 text-[oklch(0.7_0.14_280)]" />
            <div>
              <div className="text-2xl font-bold">{hexData?.total_synergy.toFixed(2) || "0.29"}</div>
              <div className="text-xs text-muted-foreground">Synergy Score</div>
            </div>
          </div>
        </motion.div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {/* Archetype Grid by Cluster */}
            <div className="space-y-12">
              {Object.entries(groupedByCluster).map(([cluster, nodes], clusterIndex) => (
                <motion.div
                  key={cluster}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + clusterIndex * 0.1 }}
                >
                  <div className="flex items-center gap-3 mb-6">
                    <div className={`w-4 h-4 rounded-full bg-gradient-to-br ${clusterColors[cluster] || clusterColors.applied_tech}`} />
                    <h2 className="text-2xl font-bold">{clusterLabels[cluster] || cluster}</h2>
                    <span className="text-sm text-muted-foreground">({nodes.length} archetypes)</span>
                  </div>
                  
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {nodes.map((node) => (
                      <motion.div
                        key={node.id}
                        whileHover={{ scale: 1.02, y: -4 }}
                        onClick={() => setSelectedArchetype(selectedArchetype?.id === node.id ? null : node)}
                        className={`neural-card p-6 cursor-pointer transition-all ${
                          selectedArchetype?.id === node.id ? "ring-2 ring-primary" : ""
                        }`}
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${clusterColors[node.cluster] || clusterColors.applied_tech} 
                                        flex items-center justify-center`}>
                            <Hexagon className="w-6 h-6 text-white" />
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold">{node.corpus_size_gb} GB</div>
                            <div className="text-xs text-muted-foreground">Corpus</div>
                          </div>
                        </div>
                        
                        <h3 className="text-xl font-bold mb-2">{node.name}</h3>
                        
                        <div className="flex flex-wrap gap-1 mb-4">
                          {node.domains.slice(0, 4).map((domain) => (
                            <span
                              key={domain}
                              className="px-2 py-0.5 text-xs rounded-full bg-primary/10 text-primary"
                            >
                              {domain}
                            </span>
                          ))}
                        </div>

                        {/* Face Affinities (expanded) */}
                        {selectedArchetype?.id === node.id && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            className="pt-4 border-t border-border/50"
                          >
                            <div className="text-sm font-medium mb-2 text-muted-foreground">
                              6-Face Affinities
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              {Object.entries(node.face_affinities).map(([face, value]) => (
                                <div key={face} className="flex items-center gap-2">
                                  <div className="flex-1">
                                    <div className="text-xs text-muted-foreground capitalize">
                                      {face.toLowerCase()}
                                    </div>
                                    <div className="h-1.5 rounded-full bg-border overflow-hidden">
                                      <div
                                        className="h-full bg-primary rounded-full"
                                        style={{ width: `${value * 100}%` }}
                                      />
                                    </div>
                                  </div>
                                  <span className="text-xs font-mono">{(value * 100).toFixed(0)}%</span>
                                </div>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
