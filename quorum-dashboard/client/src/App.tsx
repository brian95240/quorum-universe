import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import Intersections from "./pages/Intersections";
import Apex from "./pages/Apex";
import Archetypes from "./pages/Archetypes";
import Tribunal from "./pages/Tribunal";
import Synergies from "./pages/Synergies";
import Metrics from "./pages/Metrics";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/archetypes" component={Archetypes} />
      <Route path="/tribunal" component={Tribunal} />
      <Route path="/synergies" component={Synergies} />
      <Route path="/metrics" component={Metrics} />
      <Route path={"/intersections"} component={Intersections} />
      <Route path={"/apex"} component={Apex} />
      <Route path={"/404"} component={NotFound} />     <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
