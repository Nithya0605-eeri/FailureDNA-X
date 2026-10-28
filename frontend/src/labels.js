// Shared names and colours for the dashboard. Tell your teammate before changing these.
export const FAULTS = ["thermal_throttling", "memory_pressure", "network_congestion", "no_fault"];

export const FAULT_LABEL = {
  thermal_throttling: "Thermal throttling",
  memory_pressure: "Memory pressure",
  network_congestion: "Network congestion",
  no_fault: "No fault",
};

export const FAULT_COLOR = {
  thermal_throttling: "#f97316",
  memory_pressure: "#a855f7",
  network_congestion: "#38bdf8",
  no_fault: "#94a3b8",
};

export const MODE_LABEL = {
  nemotron: "Nemotron agent",
  infogain: "Info-gain heuristic",
  fixed_early: "Fixed checklist + early stop",
  fixed: "Fixed checklist (all tests)",
};

export const pct = (x) => `${Math.round((x || 0) * 100)}%`;