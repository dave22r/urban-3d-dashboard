export interface Building {
  id: number;
  struct_id: string;
  stage: string;
  height: number;
  footprint: [number, number][];
  centroid?: [number, number];
}

export interface QueryResult {
  ids: number[];
  count: number;
  filter?: {
    attribute: string;
    operator: string;
    value: number | string;
  };
  filters?: Array<{
    attribute: string;
    operator: string;
    value: number | string;
  }>;
  error?: string;
}

export interface HealthStatus {
  status: string;
  buildings_loaded: number;
  llm_available: boolean;
  llm_provider: string;
}
