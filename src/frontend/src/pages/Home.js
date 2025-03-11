import React from "react";
import { Link } from "react-router-dom";
import "../App.css";

const Home = () => {
  return (
    <div className="page-container">
      <div className="content-box">
      <h1 className="title">SynthLens</h1>
      <p className="tagline">"Transforming Pixels into Possibilities.."</p>
      <div className="buttons">
          <Link to="/signup"><button className="btn btn-primary">Sign Up</button></Link>
          <Link to="/login"><button className="btn btn-secondary">Log In</button></Link>
        </div>
    </div>
  </div>
  );
};

export default Home;