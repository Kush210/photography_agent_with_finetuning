import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css"; // Import existing styles
import { API_BASE_URL } from "../config";
const Dashboard = () => {
  const [trainingJobs, setTrainingJobs] = useState([]);
  const navigate = useNavigate();
  const userId = localStorage.getItem("user_id");

  useEffect(() => {
    if (!userId) {
      alert("Please log in first.");
      navigate("/login");
      return;
    }

    const fetchTrainingJobs = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/get_user_uploads/?user_id=${encodeURIComponent(userId)}`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });
        if (!response.ok) throw new Error("Failed to fetch training jobs");
        const data = await response.json();
        setTrainingJobs(data.uploads || []);

      } catch (error) {
        console.error("Error fetching training jobs:", error);
      }
    };

    fetchTrainingJobs();
    const interval = setInterval(fetchTrainingJobs, 60000);
    return () => clearInterval(interval);
  }, [userId, navigate]);

  const startTraining = async (projectLabel) => {
    try {
      const response = await fetch(`${API_BASE_URL}/start_training/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, project_label: projectLabel }),
      });

      if (!response.ok) throw new Error("Failed to start training");

      alert(`Training started for ${projectLabel}`);
      setTrainingJobs(prevJobs =>
        prevJobs.map(job =>
          job.project_label === projectLabel ? { ...job, training_status: "training" } : job
        )
      );
    } catch (error) {
      console.error("Error starting training:", error);
      alert("Error starting training.");
    }
  };

  const refreshStatus = async (projectLabel) => {
    try {
      const response = await fetch(`${API_BASE_URL}/check_training_status/?user_id=${encodeURIComponent(userId)}&project_label=${encodeURIComponent(projectLabel)}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) throw new Error("Failed to check training status");

      const data = await response.json();
      setTrainingJobs(prevJobs =>
        prevJobs.map(job =>
          job.project_label === projectLabel
            ? { ...job, training_status: data.status, trained_model_url: data.trained_model_url || job.trained_model_url }
            : job
        )
      );
    } catch (error) {
      console.error("Error refreshing training status:", error);
      alert("Error refreshing training status.");
    }
  };

  const goToInference = (project_label) => {
    navigate(`/inference?project_label=${project_label}`);
  };

  return (
    <div className="page-container">
      <div className="content-box">
        <h2>Dashboard</h2>
        <p>Manage your training projects</p>

        {trainingJobs.length === 0 ? (
          <p>No projects uploaded yet.</p>
        ) : (
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Project Name</th>
                <th>Status</th>
                <th>Uploaded At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {trainingJobs.map(job => (
                <tr key={job.id}>
                  <td>{job.project_label}</td>
                  <td className={`status-${job.training_status}`}>{job.training_status}</td>
                  <td>{new Date(job.upload_time).toLocaleString()}</td>
                  <td>
                    {job.training_status === "pending" ? (
                      <button className="btn-primary" onClick={() => startTraining(job.project_label)}>Start Training</button>
                    ) : job.training_status === "training" ? (
                      <>
                        <button className="btn-secondary" onClick={() => refreshStatus(job.project_label)}>Refresh Status</button>
                      </>
                    ) : job.training_status === "completed" ? (
                      <>
                        <button className="btn-success" onClick={() => goToInference(job.project_label)}>Infer Model</button>
                      </>
                    ) : (
                      <button className="btn-disabled" disabled>{job.training_status}</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Dashboard;