import React, { useState } from "react";
import { addKnown, addUnknown } from "../utils/api";
import "../App.css";

export default function SnapshotCard({ row }) {
  const [showNameInput, setShowNameInput] = useState(false);
  const [newName, setNewName] = useState("");

  // Use correct backend URL for images
  const imgSrc =
    row.snapshot_url;
  console.log(row.snapshot_url)

  const handleAddKnown = async () => {
    try {
      await addKnown(row.id, row.name);
      alert(`✅ ${row.name} added to dataset`);
    } catch (error) {
      alert("❌ Failed to add known face.");
      console.error(error);
    }
  };

  const handleAddUnknown = async () => {
    if (!newName.trim()) {
      alert("⚠️ Please enter a valid name.");
      return;
    }
    try {
      await addUnknown(row.id, newName);
      alert(`✅ ${newName} added to dataset`);
      setShowNameInput(false);
      setNewName("");
    } catch (error) {
      alert("❌ Failed to save unknown face.");
      console.error(error);
    }
  };

  return (
    <div className="snapshot-card">
      <img
        src={row.snapshot_url}
        alt={row.name || "Unknown"}
        className="snapshot-img"
        onError={(e) => (e.target.src = "/placeholder.jpg")}
      />

      <p className="snapshot-caption">
        {row.status || "Intruder"}: {row.name || "Unknown"} <br />
        <small>@ {row.timestamp || "—"}</small>
      </p>

      {row.name && row.name !== "Unknown" ? (
        <button className="btn btn-primary" onClick={handleAddKnown}>
          Promote to Dataset
        </button>
      ) : (
        <>
          <button
            className="btn btn-secondary"
            onClick={() => setShowNameInput(!showNameInput)}
          >
            Add to Known Faces
          </button>
          {showNameInput && (
            <div className="input-group">
              <input
                type="text"
                placeholder="Enter name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="input-box"
              />
              <button className="btn btn-primary" onClick={handleAddUnknown}>
                Save
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
