import React from "react";
import "../App.css";

export default function LogsTable({ logs }) {
  return (
    <table className="logs-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Status</th>
          <th>Timestamp</th>
        </tr>
      </thead>
      <tbody>
        {logs.map((row) => (
          <tr key={row.id}>
            <td>{row.id}</td>
            <td>{row.name}</td>
            <td className={row.status === "intruder" ? "alert" : "safe"}>{row.status}</td>
            <td>{row.timestamp}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
