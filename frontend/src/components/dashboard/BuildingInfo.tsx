import { X, Building2, Ruler, Tag, Hash, MapPin } from "lucide-react";
import { Building } from "@/types/building";
import { Button } from "@/components/ui/button";

interface BuildingInfoProps {
  building: Building;
  onClose: () => void;
  isFiltered: boolean;
}

export function BuildingInfo({ building, onClose, isFiltered }: BuildingInfoProps) {
  const infoItems = [
    { label: "Building ID", value: building.id, icon: Hash },
    { label: "Structure ID", value: building.struct_id || "N/A", icon: Tag },
    { label: "Stage", value: building.stage || "Unknown", icon: MapPin },
    { label: "Height", value: `${building.height.toFixed(2)} m`, icon: Ruler },
  ];

  return (
    <div className="glass-panel rounded-xl p-4 animate-slide-in-right glow-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-highlight/20 flex items-center justify-center">
            <Building2 className="w-4 h-4 text-highlight" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">Building Details</h3>
            {isFiltered && (
              <span className="text-xs text-primary">Matches filter</span>
            )}
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="h-8 w-8 text-muted-foreground hover:text-foreground"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      <div className="space-y-3">
        {infoItems.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between py-2 border-b border-border/50 last:border-0"
          >
            <div className="flex items-center gap-2">
              <item.icon className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{item.label}</span>
            </div>
            <span className="text-sm font-medium text-foreground">{item.value}</span>
          </div>
        ))}
      </div>

      {/* Height visualization bar */}
      <div className="mt-4 pt-4 border-t border-border/50">
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
          <span>Height Relative to Max (162m)</span>
          <span>{((building.height / 162) * 100).toFixed(0)}%</span>
        </div>
        <div className="h-2 bg-secondary rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-highlight rounded-full transition-all duration-500"
            style={{ width: `${Math.min((building.height / 162) * 100, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}
