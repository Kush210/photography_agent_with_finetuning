from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import storage, firestore
from google.cloud.storage import Blob
from auth import users_collection, hash_password, authenticate_user
from training import start_flux_training, check_training_status
from email_utils import send_training_completion_email
import time
import threading
import uuid
import logging
import replicate
from pydantic import BaseModel
from datetime import datetime
from typing import List
import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv(
#     "GOOGLE_APPLICATION_CREDENTIALS"
# )

replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

# Initialize Google Cloud Storage and Firestore clients
db = firestore.Client(database="photo-agent-users")
storage_client = storage.Client()
bucket_name = "flux-dev-user-images"
bucket = storage_client.bucket(bucket_name)

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change this for security)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)


class UserProfile(BaseModel):
    email: str
    password: str


@app.get("/")
async def root():
    return {"message": "Welcome to SynthLens AI Backend"}


@app.post("/signup/")
async def signup(user: UserProfile):
    try:
        user_ref = users_collection.document(user.email)
        if user_ref.get().exists:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = hash_password(user.password)
        user_ref.set({"email": user.email, "password": hashed_password})
        logger.info(f"User {user.email} registered successfully.")

        return {"message": "User registered successfully"}

    except Exception as e:
        logger.error(f"Signup error: {e}")
        return JSONResponse(content={"error": "Signup failed"}, status_code=500)


@app.post("/login/")
async def login(user: UserProfile):
    try:
        token = authenticate_user(user.email, user.password)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {"token": token, "user_id": user.email}  # Return user ID for storage

    except Exception as e:
        logger.error(f"Login error: {e}")
        return JSONResponse(content={"error": "Login failed"}, status_code=500)


@app.post("/upload/")
async def upload_images(
    user_id: str = Form(...),
    project_label: str = Form(...),
    person1_images: List[UploadFile] = File(...),
    person1_descriptions: List[str] = Form(...),
    person2_images: List[UploadFile] = File(...),
    person2_descriptions: List[str] = Form(...),
    both_images: List[UploadFile] = File(...),
    both_descriptions: List[str] = Form(...),
):
    """Uploads images to GCP Storage and saves metadata in Firestore."""

    logger.info(
        f"Received upload request for user: {user_id}, project: {project_label}"
    )
    try:
        # Validate input lengths
        if (
            len(person1_images) != 5
            or len(person2_images) != 5
            or len(both_images) != 5
            or len(person1_descriptions) != 5
            or len(person2_descriptions) != 5
            or len(both_descriptions) != 5
        ):
            logger.warning("Incorrect number of images/descriptions")
            raise HTTPException(
                status_code=400,
                detail="You must upload exactly 5 images and descriptions per category.",
            )

        # Ensure user exists
        user_ref = db.collection("users").document(user_id)
        if not user_ref.get().exists:
            logger.warning(f"User {user_id} not found in Firestore")
            raise HTTPException(status_code=404, detail="User not found")

        image_data = {}
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

        # Function to upload images
        def upload_to_gcp(file: UploadFile, category: str):
            """Uploads a single image to GCP Storage and returns its URL."""
            file_extension = os.path.splitext(file.filename)[-1]
            file_name = f"{user_id}/{project_label}/{category}/{timestamp}_{uuid.uuid4()}{file_extension}"
            blob = bucket.blob(file_name)

            logger.info(f"Uploading {file.filename} to {file_name}")
            try:
                blob.upload_from_file(file.file, content_type=file.content_type)
                image_url = f"https://storage.googleapis.com/{bucket_name}/{file_name}"
                logger.info(f"Uploaded {file.filename} successfully: {image_url}")
                return image_url
            except Exception as e:
                logger.error(f"Failed to upload {file.filename}: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Error uploading image: {e}"
                )

        # Upload images and store URLs
        for category, image_list, desc_list in [
            ("person1", person1_images, person1_descriptions),
            ("person2", person2_images, person2_descriptions),
            ("both", both_images, both_descriptions),
        ]:
            image_data[category] = [
                {"url": upload_to_gcp(img, category), "description": desc}
                for img, desc in zip(image_list, desc_list)
            ]

        # Store metadata in Firestore
        try:
            doc_ref = user_ref.collection("training_jobs").document(project_label)
            doc_ref.set(
                {
                    "user_id": user_id,
                    "project_label": project_label,
                    "upload_time": datetime.utcnow().isoformat(),
                    "training_status": "pending",
                    "trained_model_url": "",
                    "images": image_data,
                }
            )

            logger.info(f"Metadata stored successfully for {user_id}/{project_label}")
            return JSONResponse(
                content={"message": "Upload successful", "image_urls": image_data},
                status_code=200,
            )

        except Exception as e:
            logger.error(f"Error uploading metadata to Firestore: {e}")
            return JSONResponse(
                content={"error": f"Error uploading metadata: {str(e)}"},
                status_code=500,
            )

    except HTTPException as e:
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        return JSONResponse(
            content={"error": "Unexpected error occurred"}, status_code=500
        )


@app.get("/get_user_uploads/")
async def get_user_uploads(user_id: str = Query(...)):
    """
    Retrieves all uploaded images and their metadata for a user.
    """
    try:
        user_ref = db.collection("users").document(user_id)
        if not user_ref.get().exists:
            raise HTTPException(status_code=404, detail="User not found")

        uploads_ref = user_ref.collection("training_jobs")
        docs = uploads_ref.stream()

        uploads = [{"id": doc.id, **doc.to_dict()} for doc in docs]

        return JSONResponse(content={"uploads": uploads}, status_code=200)

    except HTTPException as e:
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

    except Exception as e:
        logger.error(f"Error retrieving user uploads: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


class PorjectRequest(BaseModel):
    user_id: str
    project_label: str


@app.post("/start_training/")
async def start_training(request: PorjectRequest):
    """Starts model training for a project"""
    try:
        user_id = request.user_id
        project_label = request.project_label
        user_ref = db.collection("users").document(user_id)
        job_ref = user_ref.collection("training_jobs").document(project_label)

        job = job_ref.get()
        if not job.exists:
            raise HTTPException(status_code=404, detail="Project not found")

        # Simulate training process
        response = start_flux_training(user_id, project_label)

        job_ref.update({"training_status": "training"})

        JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error(f"Error starting training: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/check_training_status/")
async def check_training_status_endpoint(
    user_id: str = Query(...), project_label: str = Query(...)
):
    """Checks the training status of a project"""
    try:
        status, trained_model_url = check_training_status(user_id, project_label)

        if status == "completed":
            return JSONResponse(
                content={
                    "status": status,
                    "message": "Training completed successfully",
                    "trained_model_url": trained_model_url,
                },
                status_code=200,
            )
        elif status == "error":
            raise HTTPException(status_code=500, detail="Error during training")
        else:
            return JSONResponse(
                content={"status": status, "message": "Training in progress"},
                status_code=202,
            )

    except HTTPException as e:
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)


class GenerateImageRequest(BaseModel):
    user_id: str
    project_label: str
    prompt: str


@app.post("/generate_image/")
async def generate_image(request: GenerateImageRequest):
    """Generates an image using the trained model"""
    user_id = request.user_id
    project_label = request.project_label
    prompt = request.prompt

    try:
        user_ref = db.collection("users").document(user_id)
        job_ref = user_ref.collection("training_jobs").document(project_label)

        job = job_ref.get()
        if not job.exists:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if the model is ready
        job_data = job.to_dict()
        trained_model_url = job_data.get("trained_model_url")

        if not trained_model_url:
            raise HTTPException(status_code=400, detail="Model not yet trained.")
        # Generate image using Replicate
        try:

            output = replicate_client.run(
                trained_model_url,
                input={
                    "prompt": prompt,
                    "num_inference_steps": 28,
                    "guidance_scale": 7.5,
                    "model": "dev",
                },
            )
            print("returned output url: ", output)
            # Convert FileOutput object to a list of URLs
            if isinstance(output, list):
                image_urls = [
                    str(item) for item in output
                ]  # Extract URLs from FileOutput objects
            else:
                image_urls = [str(output)]
            return JSONResponse(content={"image_url": image_urls}, status_code=200)

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise HTTPException(status_code=500, detail="Error generating image.")

    except HTTPException as e:
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


def monitor_training_status():
    """Background task to monitor training status and send email when completed."""
    while True:
        try:
            users_ref = db.collection("users").stream()
            for user_doc in users_ref:
                user_id = user_doc.id
                jobs_ref = user_doc.reference.collection("training_jobs").stream()

                for job in jobs_ref:
                    job_data = job.to_dict()
                    project_label = job_data.get("project_label")
                    training_id = job_data.get("replicate_training_id")
                    training_status = job_data.get("training_status")

                    # Skip if training is already completed
                    if training_status == "completed":
                        logger.info(f"Training for {project_label} completed.")
                        continue

                    if training_id:
                        training = replicate_client.trainings.get(training_id)

                        # If training is complete, update Firestore and send an email
                        if training.status == "succeeded":
                            trained_model_url = training.output.get("version", "")

                            # Update Firestore
                            job.reference.update(
                                {
                                    "training_status": "completed",
                                    "trained_model_url": trained_model_url,
                                }
                            )

                            # Send notification email
                            send_training_completion_email(user_id, project_label)
                            logger.info(
                                f"Training for {project_label} completed. Email sent to {user_id}."
                            )
                        logger.info(
                            f"Training for {project_label} is {training.status}."
                        )

        except Exception as e:
            logger.error(f"Error monitoring training status: {e}")

        # Wait before checking again (e.g., every 5 minutes)
        time.sleep(300)  # Check every 5 minutes


threading.Thread(target=monitor_training_status, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Default to 8000 if not set
    uvicorn.run(app, host="0.0.0.0", port=8080)
