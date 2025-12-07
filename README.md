classDiagram
    %% Backend Classes
    class FlaskApp {
        -buildings: List~Building~
        -GROQ_API_KEY: str
        -NUMERIC_ATTRS: Set
        -STRING_ATTRS: Set
        +api_query() JSON
        +api_buildings() JSON
        +api_health() JSON
    }

    class DataLoader {
        -DATA_PATH: str
        +load_buildings() List~Building~
    }

    class LLMService {
        -GROQ_API_KEY: str
        +query_llm(prompt: str) str
        +parse_query_fallback(prompt: str) str
        -SYSTEM_PROMPT: str
    }

    class QueryProcessor {
        +extract_json_block(text: str) dict
        +apply_single_filter(building, attr, op, val) bool
        +apply_numeric(building, attr, op, val) bool
        +apply_string(building, attr, op, val) bool
        +handle_compound_query(filters) JSON
        +handle_superlative(attr, op) JSON
        +coerce_number(value) float
    }

    class Building {
        +id: int
        +osm_id: str
        +footprint: List~List~float~~
        +height: float
        +stage: str
        +centroid_lon: float
        +centroid_lat: float
        +roll_number: str
        +address: str
        +assessed_value: float
        +assessment_class: str
        +community: str
        +land_use_designation: str
        +property_type: str
        +land_size_sm: float
        +land_size_ac: float
        +sub_property_use: str
    }

    %% Frontend Classes
    class Index {
        +render() JSX.Element
    }

    class useBuildings {
        -buildings: Building[]
        -filteredIds: number[]
        -selectedBuilding: Building
        -loading: boolean
        -queryLoading: boolean
        -error: string
        -lastQuery: QueryResult
        -health: HealthStatus
        -stats: Stats
        +runQuery(query: string) Promise
        +clearFilters() void
        +setSelectedBuilding(building) void
    }

    class CityScene {
        -buildings: Building[]
        -filteredIds: number[]
        -selectedId: number
        -onSelectBuilding: Function
        +render() JSX.Element
    }

    class BuildingMesh {
        -building: Building
        -isSelected: boolean
        -isFiltered: boolean
        -hovered: boolean
        -meshRef: THREE.Mesh
        -geometry: THREE.ExtrudeGeometry
        +handleClick(event) void
        +getColor() string
        +render() JSX.Element
    }

    class QueryInput {
        -query: string
        -loading: boolean
        -hasFilters: boolean
        -EXAMPLE_QUERIES: string[]
        +handleSubmit() void
        +handleKeyDown(event) void
        +handleExampleClick(example) void
        +handleClear() void
        +render() JSX.Element
    }

    class Sidebar {
        -stats: Stats
        -lastQuery: QueryResult
        -selectedBuilding: Building
        -filteredIds: number[]
        +render() JSX.Element
    }

    class StatsPanel {
        -stats: Stats
        -lastQuery: QueryResult
        +render() JSX.Element
    }

    class BuildingDetails {
        -building: Building
        +render() JSX.Element
    }

    class Header {
        -health: HealthStatus
        -buildingCount: number
        +render() JSX.Element
    }

    %% Type Definitions
    class BuildingInterface {
        <<interface>>
        +id: number
        +osm_id?: string
        +footprint: number[][]
        +height: number
        +stage: string
        +assessed_value?: number
        +land_use_designation?: string
        +community?: string
        +address?: string
    }

    class QueryResult {
        <<interface>>
        +ids: number[]
        +count: number
        +error?: string
        +filter?: any
        +filters?: any[]
    }

    class HealthStatus {
        <<interface>>
        +status: string
        +buildings_loaded: number
        +llm_available: boolean
        +llm_provider: string
    }

    class Stats {
        <<interface>>
        +total: number
        +filtered: number
        +avgHeight: number
        +maxHeight: number
        +minHeight: number
    }

    %% Relationships
    FlaskApp --> DataLoader
    FlaskApp --> LLMService
    FlaskApp --> QueryProcessor
    DataLoader --> Building
    useBuildings --> BuildingInterface
    CityScene --> BuildingMesh
    Sidebar --> QueryInput
    Sidebar --> StatsPanel
    Sidebar --> BuildingDetails
