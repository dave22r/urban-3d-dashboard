``` mermaid
flowchart LR
    subgraph Browser["User Browser"]
        UI[React + Three.js Frontend\n(Vercel Deployment)]
    end

    subgraph Backend["Flask API (Render.com)"]
        API[/GET /api/buildings /\nPOST /api/query /\nGET /api/health/]
        Data[buildings.json\n(preprocessed dataset)]
        Logic[Query Processor\n(Filter Engine)]
        LLMService[LLM Service\n(Groq API call)]
    end

    subgraph External["External Services"]
        Groq[Groq LLM API\nLlama 3.3 70B]
    end

    UI -->|Fetch Buildings| API
    API --> Data
    UI -->|User Query| API
    API --> Logic --> LLMService --> Groq
    Groq --> LLMService --> Logic --> API --> UI

    UI -->|Render Buildings| ThreeJS[Three.js Rendering Engine]
```
