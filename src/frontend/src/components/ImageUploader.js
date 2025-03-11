import React, { useState } from "react";

const ImageUploader = ({ category, onImageChange }) => {
    const [previews, setPreviews] = useState([]);

    const handleImageUpload = (event) => {
        const files = Array.from(event.target.files);
        if (files.length !== 5) {
            alert(`Please upload exactly 5 images for ${category}`);
            return;
        }
        setPreviews(files.map((file) => URL.createObjectURL(file)));
        onImageChange(category, files);
    };

    return (
        <div className="image-uploader">
            <h3>{category}</h3>
            <input type="file" multiple accept="image/*" onChange={handleImageUpload} />
            <div className="preview-container">
                {previews.map((src, index) => (
                    <img key={index} src={src} alt={`Preview ${index}`} className="preview-image" />
                ))}
            </div>
        </div>
    );
};

export default ImageUploader;
