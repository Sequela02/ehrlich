import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { MolViewer3D } from "@/features/molecule/MolViewer3D";
import BindingScatter from "@/features/visualization/charts/BindingScatter";
import ADMETRadar from "@/features/visualization/charts/ADMETRadar";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { FlaskConical, Microscope, FileText, ArrowRight, BrainCircuit, Rotate3D } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { CAFFEINE_SDF } from "@/shared/lib/constants";

const SCREENING_DATA = {
    points: Array.from({ length: 40 }, (_, i) => ({
        name: `Hit-${i + 1}`,
        x: Math.random() * -14 - 2, // Binding Energy
        y: Math.random() * 8 - 4,   // LogS
        smiles: "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
    })),
    x_label: "Binding Affinity (kcal/mol)",
    y_label: "Solubility (LogS)"
};

const OPTIMIZATION_DATA = {
    compound: "Lead-042",
    properties: [
        { axis: "Potency", value: 0.92 },
        { axis: "Solubility", value: 0.76 },
        { axis: "Toxicity", value: 0.15 },
        { axis: "Metab. Stab.", value: 0.82 },
        { axis: "Permeability", value: 0.68 },
    ]
};

export function CapabilitiesGallery() {
    return (
        <section className="space-y-8 py-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-2">
                    <h2 className="text-3xl font-bold tracking-tight">Capabilities by Domain</h2>
                    <p className="text-muted-foreground max-w-2xl text-lg">
                        Explore how the engine visualizes data across different stages of drug discovery.
                    </p>
                </div>
                <div className="hidden md:block">
                    <Button variant="outline" className="gap-2">
                        View Full Catalog <ArrowRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            <Tabs defaultValue="screening" className="w-full">
                <TabsList className="grid w-full grid-cols-3 lg:w-[600px] h-11">
                    <TabsTrigger value="screening" className="text-sm">Virtual Screening</TabsTrigger>
                    <TabsTrigger value="design" className="text-sm">Lead Optimization</TabsTrigger>
                    <TabsTrigger value="synthesis" className="text-sm">Evidence Synthesis</TabsTrigger>
                </TabsList>

                {/* Content Area */}
                <div className="mt-8">
                    {/* 1. Virtual Screening */}
                    <TabsContent value="screening" className="mt-0 focus-visible:outline-none">
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                            <div className="lg:col-span-4 space-y-6">
                                <div className="space-y-4">
                                    <h3 className="text-2xl font-semibold flex items-center gap-2">
                                        <Microscope className="h-6 w-6 text-primary" />
                                        High-Throughput Analysis
                                    </h3>
                                    <p className="text-muted-foreground leading-relaxed">
                                        Automatically dock and score thousands of candidates. The engine visualizes the trade-off workspace, allowing you to quickly identify high-affinity hits that maintain druggable physicochemical properties.
                                    </p>
                                </div>
                                <Card className="bg-muted/50 border-dashed">
                                    <CardHeader>
                                        <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">Workflow Input</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <code className="text-xs bg-background p-3 rounded-md block border border-border">
                                            Target: EGFR (PDB: 1M17)<br />
                                            Library: ChEMBL (Kinase Set)<br />
                                            Constraints: MW &lt; 500, LogP &lt; 5
                                        </code>
                                    </CardContent>
                                </Card>
                            </div>
                            <div className="lg:col-span-8">
                                <Card className="h-full shadow-md border-primary/10 bg-gradient-to-br from-background to-muted/20">
                                    <CardContent className="p-6">
                                        <BindingScatter
                                            data={SCREENING_DATA}
                                            title="Hit Selection: Affinity vs. Solubility"
                                        />
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    </TabsContent>

                    {/* 2. Lead Optimization */}
                    <TabsContent value="design" className="mt-0 focus-visible:outline-none">
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                            <div className="lg:col-span-4 space-y-6">
                                <div className="space-y-4">
                                    <h3 className="text-2xl font-semibold flex items-center gap-2">
                                        <FlaskConical className="h-6 w-6 text-accent" />
                                        Multi-Parameter Optimization
                                    </h3>
                                    <p className="text-muted-foreground leading-relaxed">
                                        Drill down into specific lead candidates. Visualize their 3D conformers alongside comprehensive ADMET profiles to balance potency with safety and pharmacokinetic stability.
                                    </p>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-surface border border-border rounded-lg p-4 text-center">
                                        <span className="block text-2xl font-bold text-foreground">0.92</span>
                                        <span className="text-xs text-muted-foreground uppercase tracking-wider">QED Score</span>
                                    </div>
                                    <div className="bg-surface border border-border rounded-lg p-4 text-center">
                                        <span className="block text-2xl font-bold text-foreground">0.15</span>
                                        <span className="text-xs text-muted-foreground uppercase tracking-wider">Tox Flag</span>
                                    </div>
                                </div>
                            </div>
                            <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                                <Card className="shadow-md overflow-hidden bg-[#1a1e1a] border-[#1a1e1a]">
                                    <CardHeader className="bg-transparent pb-0 pt-3">
                                        <CardTitle className="text-xs text-muted-foreground flex items-center gap-1">
                                            <Rotate3D className="h-3 w-3" />
                                            Interactive 3D Structure
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="flex items-center justify-center p-0">
                                        <MolViewer3D molBlock={CAFFEINE_SDF} width={350} height={280} />
                                    </CardContent>
                                </Card>
                                <Card className="shadow-md">
                                    <CardHeader className="bg-muted/30 pb-4">
                                        <CardTitle className="text-sm">ADMET Profile</CardTitle>
                                    </CardHeader>
                                    <CardContent className="p-2">
                                        <ADMETRadar
                                            data={OPTIMIZATION_DATA}
                                            title="Lead-042 Properties"
                                        />
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    </TabsContent>

                    {/* 3. Evidence Synthesis */}
                    <TabsContent value="synthesis" className="mt-0 focus-visible:outline-none">
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                            <div className="lg:col-span-4 space-y-6">
                                <div className="space-y-4">
                                    <h3 className="text-2xl font-semibold flex items-center gap-2">
                                        <BrainCircuit className="h-6 w-6 text-secondary" />
                                        Knowledge Synthesis
                                    </h3>
                                    <p className="text-muted-foreground leading-relaxed">
                                        The engine reads and synthesizes thousands of papers. It extracts key relationships, validates hypotheses against literature consensus, and flags potential contradictions.
                                    </p>
                                </div>
                                <Card className="bg-secondary/5 border-secondary/20">
                                    <CardHeader>
                                        <CardTitle className="text-sm font-medium text-secondary flex items-center gap-2">
                                            <FileText className="h-4 w-4" />
                                            Auto-Generated Insight
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <p className="text-sm italic text-muted-foreground">
                                            "Constraint analysis of 142 papers suggests that EGFR inhibition in this context is primarily limited by off-target toxicity in cardiac tissue, rather than potency."
                                        </p>
                                    </CardContent>
                                </Card>
                            </div>
                            <div className="lg:col-span-8">
                                <Card className="h-full flex flex-col items-center justify-center p-12 text-center text-muted-foreground bg-muted/20 border-dashed">
                                    <div className="rounded-full bg-muted p-6 mb-4">
                                        <BrainCircuit className="h-12 w-12 text-muted-foreground/50" />
                                    </div>
                                    <h4 className="text-lg font-medium text-foreground">Knowledge Graph Visualization</h4>
                                    <p className="max-w-md mt-2 text-sm">
                                        Interactive node-link diagrams visualizing citation networks and entity relationships are generated in real-time.
                                    </p>
                                    <Button variant="outline" className="mt-6" disabled>
                                        View Example Graph (Coming Soon)
                                    </Button>
                                </Card>
                            </div>
                        </div>
                    </TabsContent>
                </div>
            </Tabs>
        </section>
    );
}
