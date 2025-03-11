import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css"; 
import { API_BASE_URL } from "../config";

const Upload = () => {
  const [projectLabel, setProjectLabel] = useState(""); 
  const [images, setImages] = useState({
    person1: [],
    person2: [],
    both: []
  });
  const [descriptions, setDescriptions] = useState({
    person1: Array(5).fill(""),
    person2: Array(5).fill(""),
    both: Array(5).fill("")
  });

  const categories = [
    { key: "person1", label: "Person 1 " },
    { key: "person2", label: "Person 2 " },
    { key: "both", label: "Both Together" }
  ];

  // Handle Image Upload
  const handleFileChange = (e, category) => {
    const files = Array.from(e.target.files);
    
    if (files.length + images[category].length > 5) {
      alert(`You can only upload exactly 5 images for ${category}.`);
      return;
    }

    setImages(prev => ({
      ...prev,
      [category]: [...prev[category], ...files].slice(0, 5)
    }));
  };

  // Handle Description Change
  const handleDescriptionChange = (category, index, value) => {
    setDescriptions(prev => ({
      ...prev,
      [category]: prev[category].map((desc, i) => (i === index ? value : desc))
    }));
  };

  const navigate = useNavigate(); 

  // Handle Submit
  const handleSubmit = async () => {
    const userId = localStorage.getItem("user_id")

    if (!userId) {
      alert("User not authenticated. Please log in.");
      return;
    }

    if (!projectLabel.trim()) {
      alert("Please enter a project label before submitting.");
      return;
    }

    for (let category of categories) {
      if (images[category.key].length !== 5) {
        alert(`Please upload exactly 5 images for ${category.label}.`);
        return;
      }
    }
    
    // Implement API call here if needed
    const formData = new FormData();
    formData.append("user_id", userId);
    formData.append("project_label", projectLabel);

    // Append images & descriptions
    categories.forEach(({ key }) => {
      images[key].forEach((file, index) => {
        formData.append(`${key}_images`, file);
        const description = descriptions[key][index] ? descriptions[key][index] : "";
        formData.append(`${key}_descriptions`, description);
      });
    });

    try {
      const response = await fetch(`${API_BASE_URL}/upload/`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Upload failed!");

      alert(`Project "${projectLabel}" successfully uploaded!`);
      navigate("/dashboard");
    } catch (error) {
      alert("Error uploading project: " + error.message);
    }
  };

  return (
    <div className="page-container">
      <div className="content-box">
        <h2>Upload Images</h2>
        <p>Enter a project label and upload exactly 5 images per category.</p>

        {/* Project Label Input */}
        <input
          type="text"
          className="project-label-input"
          placeholder="Enter project label"
          value={projectLabel}
          onChange={(e) => setProjectLabel(e.target.value)}
        />

        {categories.map(({ key, label }) => (
          <div key={key} className="upload-section">
            <h3>{label}</h3>
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={(e) => handleFileChange(e, key)}
            />

            <div className="image-preview">
              {images[key].map((file, index) => (
                <div key={index} className="image-container">
                  <img src={URL.createObjectURL(file)} alt="preview" />
                  <input
                    type="text"
                    placeholder="Add description..."
                    value={descriptions[key][index]}
                    onChange={(e) => handleDescriptionChange(key, index, e.target.value)}
                  />
                </div>
              ))}
            </div>

            <p className="count-info">
              {images[key].length} / 5 images uploaded
            </p>
          </div>
        ))}

        <button className="btn btn-primary" onClick={handleSubmit}>
          Submit Uploads
        </button>
      </div>
    </div>
  );
};

export default Upload;