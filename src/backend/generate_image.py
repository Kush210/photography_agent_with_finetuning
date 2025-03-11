from dotenv import load_dotenv
import os
import replicate
import replicate
from google.cloud import storage, firestore
import logging

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


def generate_image(
    user_id: str,
    project_label: str,
    prompt: str,
):
    """Generates an image using the trained model"""
    try:
        user_ref = db.collection("users").document(user_id)
        job_ref = user_ref.collection("training_jobs").document(project_label)

        job = job_ref.get()
        if not job.exists:
            return "Project not found"

        # Check if the model is ready
        job_data = job.to_dict()
        trained_model_url = job_data.get("trained_model_url")

        if not trained_model_url:
            return "Model not yet trained."

        # Generate image using Replicate
        try:
            print("url: ", trained_model_url)
            output = replicate_client.run(
                trained_model_url,
                input={
                    "prompt": prompt,
                    "num_inference_steps": 28,
                    "guidance_scale": 7.5,
                    "model": "dev",
                },
            )

            return {"image_url": output}
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return "Error generating image."

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return "error : " + str(e)


response = generate_image(
    "Kush2101999@gmail.com",
    "yash-kush",
    "yash-kush at a beautiful sunset over the mountains",
)
print(response)
