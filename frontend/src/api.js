const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function investigateGPU(gpu, symptoms) {
  const response = await fetch(${API_URL}/api/investigate, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      gpu,
      symptoms,
      max_tests: 3,
    }),
  });

  if (!response.ok) {
    throw new Error(
      Investigation failed: HTTP ${response.status}
    );
  }

  const data = await response.json();

  if (!data.success || !data.investigation) {
    throw new Error("Invalid investigation response");
  }

  return data.investigation;
}