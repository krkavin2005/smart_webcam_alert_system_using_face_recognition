import axios from "axios";

const API_BASE = "http://127.0.0.1:5000";

// 🧠 Build correct snapshot URL
const buildSnapshotURL = (row) => {
  if (row.snapshot && !row.snapshot.startsWith("http")) {
    return `${API_BASE}/snapshots/${row.snapshot.split("\\").pop().split("/").pop()}`;
  }
  return row.snapshot_url || null;
};

// === API FUNCTIONS ===
export const fetchLogs = async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/logs`);
    return Array.isArray(res.data)
      ? res.data.map((r) => ({
          ...r,
          snapshot_url: buildSnapshotURL(r),
        }))
      : [];
  } catch (error) {
    console.error("❌ Error fetching logs:", error);
    return [];
  }
};

export const addKnown = async (id, name) => {
  try {
    const res = await axios.post(`${API_BASE}/api/add_known`, { id, name });
    return res.data;
  } catch (error) {
    console.error("❌ Error adding known face:", error);
    return { status: "error", error };
  }
};

export const addUnknown = async (id, name) => {
  try {
    const res = await axios.post(`${API_BASE}/api/add_unknown`, { id, name });
    return res.data;
  } catch (error) {
    console.error("❌ Error labeling unknown face:", error);
    return { status: "error", error };
  }
};
