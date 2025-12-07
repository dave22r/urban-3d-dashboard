import { QueryInput } from "./QueryInput";
import { StatsPanel } from "./StatsPanel";
import { BuildingInfo } from "./BuildingInfo";
import { Building } from "@/types/building";
import { QueryResult } from "@/types/building";
import { AlertCircle, Loader2 } from "lucide-react";

interface SidebarProps {
  stats: {
    total: number;
    filtered: number;
    avgHeight: number;
    maxHeight: number;
    minHeight: number;
  };
  lastQuery: QueryResult | null;
  selectedBuilding: Building | null;
  filteredIds: number[];
  loading: boolean;
  queryLoading: boolean;
  error: string | null;
  onQuery: (query: string) => void;
  onClear: () => void;
  onCloseBuilding: () => void;
}

export function Sidebar({
  stats,
  lastQuery,
  selectedBuilding,
  filteredIds,
  loading,
  queryLoading,
  error,
  onQuery,
  onClear,
  onCloseBuilding,
}: SidebarProps) {
  return (
    <aside className="w-96 h-full flex flex-col gap-4 p-4 overflow-y-auto scrollbar-thin">
      {/* Query Input */}
      <QueryInput
        onQuery={onQuery}
        onClear={onClear}
        loading={queryLoading}
        hasFilters={filteredIds.length > 0}
      />

      {/* Error display */}
      {error && (
        <div className="glass-panel rounded-lg p-3 border-destructive/50 animate-fade-in">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="glass-panel rounded-lg p-6 flex items-center justify-center">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
          <span className="ml-2 text-muted-foreground">Loading buildings...</span>
        </div>
      )}

      {/* Stats Panel */}
      {!loading && <StatsPanel stats={stats} lastQuery={lastQuery} />}

      {/* Selected Building Info */}
      {selectedBuilding && (
        <BuildingInfo
          building={selectedBuilding}
          onClose={onCloseBuilding}
          isFiltered={filteredIds.includes(selectedBuilding.id)}
        />
      )}
    </aside>
  );
}
