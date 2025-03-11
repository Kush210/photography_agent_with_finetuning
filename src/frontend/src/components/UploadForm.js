import React, { useState } from "react";
import axios from "axios";
import ImageUploader from "./ImageUploader";
import { API_BASE_URL } from "../config";



const UploadForm = () => {
    const [userId, setUserId] = useState("");
    const [trainingJobLabel, setTrainingJobLabel] = useState("");
    const [images, setImages] = useState({
        "Person 1 (wxyz)": [],
        "Person 2 (vzze)": [],
        "Both Together": []
    });
    const [descriptions, setDescriptions] = useState({});

    const handleImageChange = (category, files) => {
        setImages((prevImages) => ({ ...prevImages, [category]: files }));
    };

    const handleDescriptionChange = (event, category, index) => {
        setDescriptions({
            ...descriptions,
            [`${category} - Image ${index + 1}`]: event.target.value,
        });
    };

    const handleSubmit = async (event) => {
        event.preventDefault();

        if (!userId || !trainingJobLabel) {
            alert("User ID and Training Job Label are required!");
            return;
        }

        const formData = new FormData();
        formData.append("user_id", userId);
        formData.append("training_job_label", trainingJobLabel);

        Object.entries(images).forEach(([category, files]) => {
            files.forEach((file) => {
                formData.append("images", file);
            });
        });

        Object.entries(descriptions).forEach(([key, value]) => {
            formData.append("descriptions", value);
        });

        try {
            const response = await axios.post("${API_BASE_URL}/upload_images/", formData);
            alert("Upload successful!");
            console.log(response.data);
        } catch (error) {
            console.error("Upload error:", error);
            alert("Upload failed.");
        }
    };

    return (
        <div className="upload-form">
            <h2>Flux-Dev AI Training App</h2>
            <input type="text" placeholder="User ID" value={userId} onChange={(e) => setUserId(e.target.value)} />
            <input type="text" placeholder="Training Job Label" value={trainingJobLabel} onChange={(e) => setTrainingJobLabel(e.target.value)} />

            {Object.keys(images).map((category) => (
                <div key={category}>
                    <ImageUploader category={category} onImageChange={handleImageChange} />
                    {[...Array(5)].map((_, index) => (
                        <textarea
                            key={index}
                            placeholder={`Description for ${category} - Image ${index + 1}`}
                            onChange={(e) => handleDescriptionChange(e, category, index)}
                        />
                    ))}
                </div>
            ))}

            <button onClick={handleSubmit}>Upload Images</button>
        </div>
    );
};

export default UploadForm;
