import { Building } from "@/types/building";

interface Props {
  building: Building | null;
}

export function BuildingDetails({ building }: Props) {
  if (!building) {
    return (
      <div className="p-4 text-muted-foreground">
        Select a building to view details.
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3 text-sm">
      <h2 className="text-lg font-semibold mb-2">Building Details</h2>

      <div><strong>Building ID:</strong> {building.id}</div>
      {building.osm_id && <div><strong>OSM ID:</strong> {building.osm_id}</div>}

      <div><strong>Height:</strong> {building.height.toFixed(2)} m</div>

      <hr className="my-3 opacity-40" />

      <h3 className="font-semibold text-primary">Parcel Information</h3>

      <div><strong>Address:</strong> {building.address ?? "Unknown"}</div>
      <div><strong>Community:</strong> {building.community ?? "Unknown"}</div>
      <div><strong>Roll Number:</strong> {building.roll_number ?? "N/A"}</div>

      <div>
        <strong>Assessed Value:</strong>{" "}
        {building.assessed_value
          ? `$${building.assessed_value.toLocaleString()}`
          : "N/A"}
      </div>

      <div><strong>Zoning:</strong> {building.land_use_designation ?? "N/A"}</div>
      <div><strong>Property Type:</strong> {building.property_type ?? "N/A"}</div>

      <div>
        <strong>Lot Size:</strong>{" "}
        {building.land_size_sm
          ? `${building.land_size_sm.toLocaleString()} m²`
          : "N/A"}
      </div>

      <div><strong>Sub-property Use:</strong> {building.sub_property_use ?? "N/A"}</div>
    </div>
  );
}