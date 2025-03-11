import React, { useState } from "react";
import { useLocation } from "react-router-dom";
import { API_BASE_URL } from "../config";

const Inference = () => {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const projectLabel  = params.get("project_label");

  const [prompt, setPrompt] = useState(`"${projectLabel}" `);;
  const [generatedImage, setGeneratedImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async (prompt) => {
    if (!prompt.trim()) {
      alert("Please enter a prompt.");
      return;
    }

    setLoading(true);
    setGeneratedImage(null); 
    try {
      const response = await fetch(`${API_BASE_URL}/generate_image/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: localStorage.getItem("user_id"),
          project_label: params.get("project_label") ,
          prompt: prompt,
        }),
      });

      if (!response.ok) throw new Error("Failed to generate image");

      const data = await response.json();
      if (data.image_url && data.image_url.length > 0) {
        console.log("Generated Image URL:", data.image_url[0]); // Debugging
        setGeneratedImage(data.image_url[0]); // Update state with image URL
      } else {
        alert("No image generated. Please try again.");
      }

    } catch (error) {
      console.error("Error generating image:", error);
      alert("Error generating image.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="content-box expanded">
        <h2>Generate Images</h2>
        <p>Use your trained model to generate images based on text prompts.</p>
        <div className="guidelines">
          <h4>📌 Prompt Guidelines:</h4>
          <ul>
            <li>✅ Always include the trigger word: <b>"{projectLabel}"</b> in your prompt.</li>
            <li>🎭 Describe the scene clearly (e.g., <i>"{projectLabel} wearing a red coat, in a futuristic city"</i>).</li>
            <li>🌄 Add background details (e.g., <i>"{projectLabel} standing in a snowy landscape"</i>).</li>
            <li>🎨 Specify style if needed (e.g., <i>"{projectLabel} in anime style, cinematic lighting"</i>).</li>
          </ul>
        </div>
        <input
          type="text"
          // eslint-disable-next-line
          placeholder={'Include "${projectLabel}" in your prompt'}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />

        <button className="btn-primary" onClick={() => handleGenerate(prompt)} disabled={loading}>
          {loading ? "Generating..." : "Generate Image"}
        </button>

        {generatedImage && (
        <div className="generated-image-container">
          <h4>Generated Image:</h4>
          <img src={generatedImage} alt="Generated result" style={{ width: "100%", maxWidth: "500px", borderRadius: "10px", marginTop: "10px" }} />
        </div>
      )}
      </div>
    </div>
  );
};

export default Inference;
