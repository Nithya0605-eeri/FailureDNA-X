import { useState } from "react";
import "./App.css";

const demoInvestigation = {
  gpu_id: "GPU-001",
  status: "suspected_fault",
  suspected_causes: ["overheating"],
  tests_completed: ["thermal_test"],
  total_test_cost: 1,
  investigation_history: [
    {
      step: 1,
      ai_selected_test: "thermal_test",
      ai_reason:
        "High temperature suggests a possible thermal issue. Run a thermal diagnostic first.",
      test_result: {
        result: "abnormal",
        measurement: {
          temperature_c: 92,
          thermal_throttling: true,
        },
        test_cost: 1,
      },
    },
  ],
};

function App() {
  const [investigation, setInvestigation] = useState(null);
  const [loading, setLoading] = useState(false);

  function startDemo() {
    setLoading(true);
    setInvestigation(null);

    // Demonstration only; real API integration comes next.
    setInvestigation(demoInvestigation);
    setLoading(false);
  }

  return (
    <div className="dashboard">
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
                {investigation.suspected_causes.join(", ")}
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