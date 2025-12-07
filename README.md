``` mermaid

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
```
Below is the Preprocessing pipeline diagram (not necessary)

``` mermaid
flowchart TD
    Start([Start Preprocessing]) --> DownloadOSM[Download OSM Data<br/>map.osm]
    Start --> DownloadParcel[Download Calgary Parcels<br/>parcels.geojson]

    DownloadOSM --> Step1[Step 1: preprocess_osm.py]
    DownloadParcel --> Step1

    subgraph "Step 1: OSM Building Extraction"
        Step1 --> ParseXML[Parse OSM XML]
        ParseXML --> ExtractNodes[Extract Node Coordinates<br/>lat, lon]
        ExtractNodes --> ExtractWays[Extract Ways with building=*]
        ExtractWays --> GetHeight[Get building:height or default 5m]
        GetHeight --> CreateFootprint[Create polygon footprint]
        CreateFootprint --> CalcCentroid[Calculate centroid]
        CalcCentroid --> OSMBuildings[(osm_buildings.json)]
    end

    OSMBuildings --> Step2[Step 2: preprocess_parcels.py]
    DownloadParcel --> Step2

    subgraph "Step 2: Parcel Filtering"
        Step2 --> LoadBBox[Load OSM bounding box]
        LoadBBox --> FilterParcels[Filter parcels by bbox]
        FilterParcels --> ExtractProps[Extract parcel properties]
        ExtractProps --> SimplifyGeom[Simplify geometry]
        SimplifyGeom --> Parcels[(parcels.json)]
    end

    Parcels --> Step3[Step 3: preprocess_join.py]
    OSMBuildings --> Step3

    subgraph "Step 3: Spatial Join"
        Step3 --> LoadBoth[Load OSM + parcel datasets]
        LoadBoth --> IterateBuildings{For each building}
        
        IterateBuildings --> GetCentroid[Get building centroid]
        GetCentroid --> BBoxCheck{Inside parcel bbox?}

        BBoxCheck -->|No| NextParcel[Try next parcel]
        NextParcel --> BBoxCheck

        BBoxCheck -->|Yes| PointInPoly[Point-in-polygon test]

        PointInPoly -->|Inside| FoundMatch[Match found!]
        PointInPoly -->|Outside| NextParcel

        FoundMatch --> MultiMatch{Multiple matches?}
        MultiMatch -->|Yes| PickBest[Pick highest assessed_value]
        MultiMatch -->|No| UseMatch[Use single match]

        PickBest --> MergeData[Merge building + parcel data]
        UseMatch --> MergeData
        
        BBoxCheck -->|No more parcels| NoMatch[Set parcel fields = null]
        NoMatch --> AddToOutput

        MergeData --> AddToOutput[Add enriched building]
        AddToOutput --> IterateBuildings

        IterateBuildings -->|Done| NormalizeCoords[Normalize to local coords]
    end

    NormalizeCoords --> FinalDataset[(buildings.json)]
    FinalDataset --> End([Ready to Load])

```
Lastly, this is the LLM Query Processing flowchart

``` mermaid
Unable to render rich display

Parse error on line 26:
... all normal filters (AND logic)] App
-----------------------^
Expecting 'SQE', 'DOUBLECIRCLEEND', 'PE', '-)', 'STADIUMEND', 'SUBROUTINEEND', 'PIPE', 'CYLINDEREND', 'DIAMOND_STOP', 'TAGEND', 'TRAPEND', 'INVTRAPEND', 'UNICODE_TEXT', 'TEXT', 'TAGSTART', got 'PS'

For more information, see https://docs.github.com/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams#creating-mermaid-diagrams
flowchart TD
    Start([User Query Received]) --> CheckEmpty{Query empty?}
    CheckEmpty -->|Yes| ReturnEmpty[Return empty result]
    CheckEmpty -->|No| CreatePrompt[Create LLM Prompt]

    CreatePrompt --> CheckAPIKey{Groq API Key?}
    CheckAPIKey -->|No| Fallback[Use Fallback Parser]
    CheckAPIKey -->|Yes| CallGroq[Call Groq API]

    CallGroq --> APIResponse{API Success?}
    APIResponse -->|Error| Fallback
    APIResponse -->|Success| ExtractResponse[Extract JSON text]

    Fallback --> RegexParse[Regex fallback processing]
    RegexParse --> ParseJSON

    ExtractResponse --> ParseJSON[Extract JSON Block]

    ParseJSON --> ValidJSON{Valid JSON?}
    ValidJSON -->|No| Error[Return parse error]

    ValidJSON -->|Yes| CheckType{Has 'filters'?}

    CheckType -->|Yes| CompoundQuery
    CheckType -->|No| SingleQuery

    %% Compound Query
    CompoundQuery --> SplitFilters[Separate superlatives & normal]
    SplitFilters --> ApplyNormal[Apply all normal filters (AND logic)]
    ApplyNormal --> SuperCheck{Superlatives exist?}
    SuperCheck -->|No| ReturnNormal
    SuperCheck -->|Yes| ApplySuperlative
    ApplySuperlative --> ReturnCompound

    %% Single Query
    SingleQuery --> OperatorCheck{Operator max/min?}
    OperatorCheck -->|Yes| SuperSingle
    OperatorCheck -->|No| RegularSingle

    SuperSingle --> ComputeExtreme[Find max/min value]
    ComputeExtreme --> ReturnSuper

    RegularSingle --> FilterBuildings[Apply numeric/string ops]
    FilterBuildings --> ReturnSingle

    %% Endpoints
    ReturnEmpty --> End
    ReturnNormal --> End
    ReturnCompound --> End
    ReturnSuper --> End
    ReturnSingle --> End
    Error --> End

```
