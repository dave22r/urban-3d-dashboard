UML Diagram

``` mermaid

flowchart TD
    Start([User Query Received]) --> CheckEmpty{Query empty}
    CheckEmpty -->|Yes| ReturnEmpty[Return empty result]
    CheckEmpty -->|No| CreatePrompt[Create LLM prompt]

    CreatePrompt --> CheckAPIKey{Groq API key exists}
    CheckAPIKey -->|No| Fallback[Use fallback parser]
    CheckAPIKey -->|Yes| CallGroq[Call Groq API]

    CallGroq --> APIResponse{API success}
    APIResponse -->|Error| Fallback
    APIResponse -->|Success| ExtractResponse[Extract JSON text]

    Fallback --> RegexParse[Run fallback regex parser]
    RegexParse --> ParseJSON

    ExtractResponse --> ParseJSON[Extract JSON block]

    ParseJSON --> ValidJSON{JSON is valid}
    ValidJSON -->|No| Error[Return parsing error]

    ValidJSON -->|Yes| CheckType{Contains filters}

    CheckType -->|Yes| CompoundQuery
    CheckType -->|No| SingleQuery

    %% Compound Query Section
    CompoundQuery --> SplitFilters[Split normal and superlative filters]
    SplitFilters --> ApplyNormal[Apply all normal filters using AND]
    ApplyNormal --> SuperCheck{Superlative filters exist}
    SuperCheck -->|No| ReturnNormal[Return normal filtered results]
    SuperCheck -->|Yes| ApplySuper[Apply superlative filters]
    ApplySuper --> ReturnCompound[Return compound query results]

    %% Single Query Section
    SingleQuery --> OpCheck{Operator is max or min}
    OpCheck -->|Yes| SuperSingle
    OpCheck -->|No| RegularSingle

    SuperSingle --> Extreme[Compute extreme value]
    Extreme --> ReturnSuper[Return superlative result]

    RegularSingle --> FilterBuildings[Apply numeric or text filtering]
    FilterBuildings --> ReturnSingle[Return single filter result]

    %% Endpoints
    ReturnEmpty --> End
    ReturnNormal --> End
    ReturnCompound --> End
    ReturnSuper --> End
    ReturnSingle --> End
    Error --> End
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


