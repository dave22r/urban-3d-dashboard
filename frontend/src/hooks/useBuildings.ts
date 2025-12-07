import { useState, useEffect, useCallback } from "react";
import { Building, QueryResult, HealthStatus } from "@/types/building";
import { API_ROUTES } from "@/config/api";


export function useBuildings() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [filteredIds, setFilteredIds] = useState<number[]>([]);
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
  const [loading, setLoading] = useState(true);
  const [queryLoading, setQueryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState<QueryResult | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  // Fetch buildings on mount
  useEffect(() => {
    const fetchBuildings = async () => {
      try {
        setLoading(true);
        const response = await fetch(API_ROUTES.BUILDINGS);
        if (!response.ok) throw new Error("Failed to fetch buildings");
        const data = await response.json();
        setBuildings(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load buildings");
        console.error("Error fetching buildings:", err);
      } finally {
        setLoading(false);
      }
    };

    const fetchHealth = async () => {
      try {
        const response = await fetch(API_ROUTES.HEALTH);
        if (response.ok) {
          const data = await response.json();
          setHealth(data);
        }
      } catch (err) {
        console.error("Health check failed:", err);
      }
    };

    fetchBuildings();
    fetchHealth();
  }, []);

  // Run natural language query
  const runQuery = useCallback(async (query: string) => {
    if (!query.trim()) {
      setFilteredIds([]);
      setLastQuery(null);
      return;
    }

    try {
      setQueryLoading(true);
      setError(null);

      const response = await fetch(API_ROUTES.QUERY, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) throw new Error("Query failed");

      const data: QueryResult = await response.json();
      
      if (data.error) {
        setError(data.error);
        setFilteredIds([]);
      } else {
        setFilteredIds(data.ids);
        setLastQuery(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
      console.error("Query error:", err);
    } finally {
      setQueryLoading(false);
    }
  }, []);

  // Clear filters
  const clearFilters = useCallback(() => {
    setFilteredIds([]);
    setLastQuery(null);
    setSelectedBuilding(null);
  }, []);

  // Calculate stats
  const stats = {
    total: buildings.length,
    filtered: filteredIds.length,
    avgHeight: buildings.length > 0 
      ? buildings.reduce((sum, b) => sum + b.height, 0) / buildings.length 
      : 0,
    maxHeight: buildings.length > 0 
      ? Math.max(...buildings.map(b => b.height)) 
      : 0,
    minHeight: buildings.length > 0 
      ? Math.min(...buildings.map(b => b.height)) 
      : 0,
  };

  return {
    buildings,
    filteredIds,
    selectedBuilding,
    setSelectedBuilding,
    loading,
    queryLoading,
    error,
    lastQuery,
    health,
    stats,
    runQuery,
    clearFilters,
  };
}