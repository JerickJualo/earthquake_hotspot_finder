import { useEffect, useState } from "react";

import { getHealth } from "./services/api";

function App() {
  const [backendState, setBackendState] = useState("checking");

  useEffect(() => {
    getHealth()
      .then(() => setBackendState("connected"))
      .catch(() => setBackendState("unavailable"));
  }, []);

  return (
    <main className="shell">
      <section className="hero-card">
        <p className="eyebrow">Phase 2 environment setup</p>
        <h1>Earthquake Hotspot Finder</h1>
        <p className="intro">
          The React and FastAPI foundations are ready. Dataset analytics and the
          interactive dashboard will be added in later phases.
        </p>
        <div className={`status status-${backendState}`}>
          Backend status: {backendState}
        </div>
      </section>
    </main>
  );
}

export default App;
