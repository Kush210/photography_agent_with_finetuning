import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../config";
import "../App.css";

const Signup = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSignup = async () => {
    try {
      const response =  await fetch(`${API_BASE_URL}/signup/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json(); // Parse JSON response
      console.log("API Response:", data); // Log response for debugging

      if (!response.ok) {
          throw new Error(data.detail || "Signup failed. Please try again.");
      }

      alert("Signup successful! Redirecting to login.");
      navigate("/login");
    } catch (error) {
      console.error("Signup error:", error);
      alert(error.response?.data?.detail || "Signup failed. Please try again.");
    }
  };

  return (
    <div className="page-container">
      <div className="content-box">
        <h2>Signup</h2>
        <input type="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
        <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
        <button className="btn btn-primary" onClick={handleSignup}>Sign Up</button>
      </div>
    </div>
  );
};

export default Signup;
