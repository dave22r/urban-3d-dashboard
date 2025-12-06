import { useEffect, useState } from "react";
import CityScene from "./CityScene";

export default function App() {
  const [buildings, setBuildings] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5000/api/buildings")
      .then(res => res.json())
      .then(data => setBuildings(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      {buildings.length > 0 ? (
        <CityScene buildings={buildings} />
      ) : (
        <div style={{ padding: 20 }}>Loading buildings...</div>
      )}
    </div>
  );
}
