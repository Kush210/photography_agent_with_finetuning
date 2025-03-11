import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../config";
import "../App.css";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/login/`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ email, password }),
              });

      const data = await response.json(); // Parse JSON response

      if (!response.ok) {
          throw new Error(data.detail || "Login failed. Please try again.");
      }
      if (!data || typeof data !== "object") {
        throw new Error("Invalid response from server.");
      }

      if (!data.token) {
          throw new Error("Login failed: No token received.");
      }

      console.log("Login successful:", data.token);

      localStorage.setItem("token", data.token)
      localStorage.setItem("user_id", data.user_id);

      alert("Login successful!");
      navigate("/upload"); 
    } catch (error) {
      console.error("Login error:", error);
      alert("Invalid credentials", error.message);
      navigate("/login");
    }
  };

  return (
    <div className="page-container">
      <div className="content-box">
      <h2>Login</h2>
      <input type="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Log In</button>
      </div>
    </div>
  );
};

export default Login;
