import { Building2, ArrowUp, ArrowDown, Filter, Ruler } from "lucide-react";
import { QueryResult } from "@/types/building";

interface StatsPanelProps {
  stats: {
    total: number;
    filtered: number;
    avgHeight: number;
    maxHeight: number;
    minHeight: number;
  };
  lastQuery: QueryResult | null;
}

export function StatsPanel({ stats, lastQuery }: StatsPanelProps) {
  const statCards = [
    {
      label: "Total Buildings",
      value: stats.total,
      icon: Building2,
      color: "text-primary",
    },
    {
      label: "Filtered",
      value: stats.filtered,
      icon: Filter,
      color: "text-highlight",
      hidden: stats.filtered === 0,
    },
    {
      label: "Max Height",
      value: `${stats.maxHeight.toFixed(1)}m`,
      icon: ArrowUp,
      color: "text-success",
    },
    {
      label: "Min Height",
      value: `${stats.minHeight.toFixed(1)}m`,
      icon: ArrowDown,
      color: "text-muted-foreground",
    },
    {
      label: "Avg Height",
      value: `${stats.avgHeight.toFixed(1)}m`,
      icon: Ruler,
      color: "text-primary",
    },
  ];

  return (
    <div className="space-y-4 animate-fade-in" style={{ animationDelay: "0.1s" }}>
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        Statistics
      </h3>
      
      <div className="grid grid-cols-2 gap-3">
        {statCards
          .filter((s) => !s.hidden)
          .map((stat) => (
            <div key={stat.label} className="stat-card">
              <div className="flex items-center gap-2 mb-2">
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
                <span className="text-xs text-muted-foreground">{stat.label}</span>
              </div>
              <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
      </div>

      {/* Last query info */}
      {lastQuery && lastQuery.filter && (
        <div className="glass-panel rounded-lg p-3 border-primary/20">
          <p className="text-xs text-muted-foreground mb-1">Applied Filter:</p>
          <code className="text-xs font-mono text-primary">
            {lastQuery.filter.attribute} {lastQuery.filter.operator} {lastQuery.filter.value}
          </code>
        </div>
      )}
    </div>
  );
}
