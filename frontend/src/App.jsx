import { useEffect, useState } from "react";
import CityScene from "./CityScene";

export default function App() {
  const [buildings, setBuildings] = useState([]);
  const [filteredIds, setFilteredIds] = useState([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    fetch("http://localhost:5000/api/buildings")
      .then((res) => res.json())
      .then((data) => setBuildings(data))
      .catch((err) => console.error(err));
  }, []);

  const runQuery = async () => {
    try {
      const res = await fetch("http://localhost:5000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      const data = await res.json();
      setFilteredIds(data.ids);
    } catch (e) {
      console.error("Query error:", e);
    }
  };

  return (
    <>
      {/* Query bar */}
      <div style={{ padding: "10px", position: "absolute", zIndex: 10 }}>
        <input
          type="text"
          placeholder="Ask a question... e.g. 'buildings over 50 meters'"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ padding: "8px", width: "300px" }}
        />
        <button
          onClick={runQuery}
          style={{ marginLeft: "8px", padding: "8px" }}
        >
          Run
        </button>
      </div>

      {/* 3D Scene */}
      <div style={{ width: "100vw", height: "100vh" }}>
        <CityScene buildings={buildings} filtered={filteredIds} />
      </div>
    </>
  );
}
