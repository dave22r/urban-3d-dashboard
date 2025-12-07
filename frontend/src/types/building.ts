export interface Building {
  id: number;
  osm_id?: string;

  // Geometry
  footprint: number[][];
  height: number;
  stage: string;

  // Centroid computed during preprocessing
  centroid_lon?: number;
  centroid_lat?: number;

  // ===== Parcel data (optional if parcel not found) =====
  roll_number?: string | null;
  address?: string | null;

  assessed_value?: number | null;
  assessment_class?: string | null;
  assessment_class_description?: string | null;

  community?: string | null;
  land_use_designation?: string | null;
  property_type?: string | null;

  land_size_sm?: number | null;
  land_size_ac?: number | null;

  sub_property_use?: string | null;
}

export interface QueryResult {
  ids: number[];
  count: number;
  error?: string;
  filter?: any;
  filters?: any[];
}

export interface HealthStatus {
  status: string;
  buildings_loaded: number;
  llm_available: boolean;
  llm_provider: string;
}