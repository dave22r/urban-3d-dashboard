// Urban 3D City Dashboard
import { Header } from "@/components/dashboard/Header";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { CityScene } from "@/components/scene/CityScene";
import { useBuildings } from "@/hooks/useBuildings";

const Index = () => {
  const {
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
  } = useBuildings();

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-background">
      {/* Header */}
      <Header health={health} buildingCount={stats.total} />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          stats={stats}
          lastQuery={lastQuery}
          selectedBuilding={selectedBuilding}
          filteredIds={filteredIds}
          loading={loading}
          queryLoading={queryLoading}
          error={error}
          onQuery={runQuery}
          onClear={clearFilters}
          onCloseBuilding={() => setSelectedBuilding(null)}
        />

        {/* 3D Scene */}
        <main className="flex-1 relative">
          <CityScene
            buildings={buildings}
            filteredIds={filteredIds}
            selectedId={selectedBuilding?.id ?? null}
            onSelectBuilding={setSelectedBuilding}
          />

          {/* Filter indicator overlay */}
          {filteredIds.length > 0 && (
            <div className="absolute top-4 right-4 glass-panel rounded-lg px-4 py-2 animate-fade-in">
              <span className="text-sm text-primary font-medium">
                {filteredIds.length} building{filteredIds.length !== 1 ? 's' : ''} highlighted
              </span>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Index;