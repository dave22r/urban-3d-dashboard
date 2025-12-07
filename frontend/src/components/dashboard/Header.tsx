import { Building2, Cpu, Database } from "lucide-react";
import { HealthStatus } from "@/types/building";

interface HeaderProps {
  health: HealthStatus | null;
  buildingCount: number;
}

export function Header({ health, buildingCount }: HeaderProps) {
  return (
    <header className="glass-panel border-b border-primary/10 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center glow-border">
              <Building2 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground glow-text">
                Calgary Urban 3D
              </h1>
              <p className="text-xs text-muted-foreground">
                City Building Dashboard
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* Status indicators */}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-primary" />
              <span className="text-muted-foreground">
                <span className="text-foreground font-medium">{buildingCount}</span> buildings
              </span>
            </div>
            
            {health && (
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-primary" />
                <span className="text-muted-foreground">
                  {health.llm_available ? (
                    <span className="text-success">LLM Active</span>
                  ) : (
                    <span className="text-highlight">Fallback Mode</span>
                  )}
                </span>
              </div>
            )}
          </div>

          {/* Connection status */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${health ? 'bg-success' : 'bg-destructive'} animate-pulse`} />
            <span className="text-xs text-muted-foreground">
              {health ? 'Connected' : 'Offline'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
