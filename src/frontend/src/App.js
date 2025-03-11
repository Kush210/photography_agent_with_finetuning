import React from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
// import { Link } from "react-router-dom";
import Home from "./pages/Home";
import Upload from "./pages/Upload";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Inference from "./pages/Inference";

// import UploadForm from "./components/UploadForm";
import Navbar from "./components/Navbar";
import "./index.css";

function App() {
    const isAuthenticated = !!localStorage.getItem("token");

    return (
        <Router>
            <Navbar />
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/signup" element={<Signup />} />
                <Route path="/login" element={<Login />} />
                {/* Protected Route - Redirects if Not Logged In */}
                <Route path="/upload" element={isAuthenticated ? <Upload /> : <Navigate to="/login" />} />
                <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
                <Route path="/inference" element={isAuthenticated ? <Inference />: <Navigate to="/login"/>} />
            </Routes>
    </Router>
    );
}

export default App;