UML Diagram

``` mermaid

classDiagram
    %% ============ BACKEND ============
    class FlaskApp {
        -buildings: List~Building~
        -GROQ_API_KEY: str
        +api_query() JSON
        +api_buildings() JSON
        +api_health() JSON
    }

    class DataLoader {
        +load_buildings() List~Building~
    }

    class LLMService {
        +query_llm(prompt) str
        +parse_query_fallback(prompt) str
    }

    class QueryProcessor {
        +extract_json_block(text) dict
        +apply_single_filter() bool
        +handle_compound_query() JSON
        +handle_superlative() JSON
    }

    class Building {
        +id: int
        +height: float
        +footprint: List~List~float~~
        +assessed_value: float
        +community: str
        +land_use_designation: str
    }

    %% ============ FRONTEND ============
    class Index {
        +render() JSX
    }

    class useBuildings {
        -buildings: Building[]
        -filteredIds: number[]
        -selectedBuilding: Building
        +runQuery(query) Promise
        +clearFilters() void
    }

    class CityScene {
        +render() JSX
    }

    class BuildingMesh {
        -building: Building
        -isSelected: bool
        -isFiltered: bool
        +handleClick() void
        +getColor() string
    }

    class Sidebar {
        +render() JSX
    }

    class QueryInput {
        -query: string
        +handleSubmit() void
    }

    class Header {
        +render() JSX
    }

    %% ============ RELATIONSHIPS ============
    %% Backend Flow
    FlaskApp --> DataLoader: uses
    FlaskApp --> LLMService: uses
    FlaskApp --> QueryProcessor: uses
    FlaskApp --> Building: manages
    DataLoader ..> Building: creates
    
    %% Frontend Flow
    Index --> useBuildings: uses
    Index --> CityScene: renders
    Index --> Sidebar: renders
    Index --> Header: renders
    
    useBuildings --> FlaskApp: API calls
    useBuildings ..> Building: manages
    
    CityScene --> BuildingMesh: contains
    BuildingMesh ..> Building: displays
    
    Sidebar --> QueryInput: contains
    QueryInput --> useBuildings: triggers
    
    %% External
    LLMService --> GroqAPI: calls
    BuildingMesh --> ThreeJS: uses
    
    class GroqAPI {
        <<external>>
    }
    
    class ThreeJS {
        <<external>>
    }
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


