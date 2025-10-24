// Dashboard.jsx
import React, { useEffect, useState } from "react";
import { fetchLogs } from "../utils/api";
import LogsTable from "./LogsTable";
import SnapshotCard from "./SnapshotCard";

export default function Dashboard() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadLogs = async () => {
      try {
        const data = await fetchLogs();
        console.log("✅ Fetched logs:", data);
        if (Array.isArray(data)) {
          setLogs(data);
          setError("");
        } else {
          setLogs([]);
          setError("Invalid data format received from API");
        }
      } catch (err) {
        console.error("❌ Error fetching logs:", err);
        setError("Failed to load logs. Please check the Flask server.");
      } finally {
        setLoading(false);
      }
    };

    loadLogs();

    // Auto-refresh every 5 seconds
    const interval = setInterval(loadLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">
      <h1>Smart Webcam Security Dashboard</h1>
      <p>Recent recognitions and alerts</p>

      {loading && <p>Loading logs...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {/* Logs Table */}
      <h2>Logs</h2>
      <div style={{ maxHeight: "600px", overflowY: "auto" }}>
        {logs.length > 0 && <LogsTable logs={logs} />}
      </div>

      {/* Snapshots Grid */}
      <h2>Latest Snapshots</h2>
      <div className="snapshot-grid">
        {logs.length > 0 ? (
          logs
            .filter((row) => row.snapshot_url) // Only valid snapshots
            .slice(0, 12)
            .map((row) => <SnapshotCard key={row.id} row={row} />)
        ) : (
          <p>No data available yet.</p>
        )}
      </div>
    </div>
  );
}
