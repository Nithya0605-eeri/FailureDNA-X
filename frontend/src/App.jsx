import { useState } from "react";
import { investigateGPU } from "./api";
import "./App.css";


function App() {
  const [investigation, setInvestigation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

async function startDemo() {
  setLoading(true);
  setInvestigation(null);
  setError("");
try {
const gpu = {
  gpu_id: "GPU-004",
  temperature_c: 55,
  memory_usage_percent: 40,
  gpu_utilization_percent: 65,
  network_latency_ms: 2.5,
};

const symptoms = {
  high_temperature: false,
  high_memory_usage: false,
  slow_network: false,
  low_gpu_utilization: false,
};

    const result = await investigateGPU(gpu, symptoms);
    setInvestigation(result);
  } catch (error) {
    console.error("Investigation failed:", error);
    setError(error.message || "Investigation failed. Please try again.");
  } finally {
    setLoading(false);
  }
}

  return (
    <div className="dashboard">
      {error && (
  <div role="alert" className="error-message">
    {error}
  </div>
)}
      <header className="header">
        <div>
          <p className="eyebrow">NVIDIA × NEBIUS AI HACKATHON</p>
          <h1>FailureDNA X</h1>
          <p className="subtitle">
            Autonomous GPU Failure Investigation
          </p>
        </div>
        <span className="status-badge">Prototype Dashboard</span>
      </header>

      <main>
        <section className="panel">
          <h2>GPU Investigation Control</h2>
          <p>
            Investigate simulated GPU failures using NVIDIA Nemotron
            and diagnostic tools.
          </p>

          <button
            onClick={startDemo}
            disabled={loading}
            className="primary-button"
          >
            {loading ? "Investigating..." : "Run Demo Investigation"}
          </button>
        </section>

        {investigation && (
          <>
            <section className="metrics-grid">
              <div className="metric-card">
                <span>GPU ID</span>
                <strong>{investigation.gpu_id}</strong>
              </div>

              <div className="metric-card">
                <span>Investigation Status</span>
                <strong>{investigation.status}</strong>
              </div>

              <div className="metric-card">
                <span>Tests Completed</span>
                <strong>{investigation.tests_completed.length}</strong>
              </div>

              <div className="metric-card">
                <span>Simulated Test Cost</span>
                <strong>{investigation.total_test_cost}</strong>
              </div>
            </section>

            <section className="panel">
              <h2>AI Diagnosis</h2>

              <p>
                <strong>Suspected Root Cause:</strong>{" "}
                {investigation.suspected_causes?.length > 0
  ? investigation.suspected_causes.join(", ")
  : "No fault detected"}
              </p>

              <p className="disclaimer">
                Demo data — not a live GPU measurement or verified diagnosis.
              </p>
            </section>

            <section className="panel">
              <h2>AI Investigation Timeline</h2>

              {investigation.investigation_history.map((item) => (
                <div className="timeline-item" key={item.step}>
                  <div className="step-number">{item.step}</div>

                  <div>
                    <h3>{item.ai_selected_test}</h3>
                    <p>{item.ai_reason}</p>

                    <span className="result-badge">
                      Result: {item.test_result.result}
                    </span>

                    <pre>
                      {JSON.stringify(
                        item.test_result.measurement,
                        null,
                        2
                      )}
                    </pre>
                  </div>
                </div>
              ))}
            </section>
          </>
        )}
      </main>

      <footer>
        FailureDNA X · NVIDIA Nemotron + Nebius Token Factory
      </footer>
    </div>
  );
}

export default App;