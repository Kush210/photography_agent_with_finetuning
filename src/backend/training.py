import replicate
import os
import replicate.client
from prepare_dataset import prepare_flux_dataset
from google.cloud import firestore
from dotenv import load_dotenv
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv(
#     "GOOGLE_APPLICATION_CREDENTIALS"
# )
load_dotenv()


def start_flux_training(user_id, project_label):
    """Triggers fine-tuning of the Flux model on Replicate API."""

    dataset_url, error = prepare_flux_dataset(user_id, project_label)
    if error:
        return {"error": error}

    replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_KEY"))

    user = user_id.split("@")[0].lower()
    project_name = project_label.lower()
    name = f"{user[:6]}-{project_name}"

    model = replicate_client.models.create(
        owner="kush210",
        name=name,
        visibility="private",  # or "private" if you prefer
        hardware="gpu-t4",  # Replicate will override this for fine-tuned models
        description=f"A fine-tuned FLUX.1 model for {user_id} - {project_label}",
    )

    training = replicate_client.trainings.create(
        version="ostris/flux-dev-lora-trainer:4ffd32160efd92e956d39c5338a9b8fbafca58e03f791f6d8011f3e20e8ea6fa",
        input={
            "input_images": dataset_url,
            "trigger_word": f"{project_label}",
            "optimizer": "adamw8bit",
            "lora_rank": 32,
            "steps": 1000,
            "learning_rate": 5e-5,
            "batch_size": 4,
            "resolution": "1024",
            "autocaption": True,
            "hf_token": os.getenv("HUGGING_FACE_TOKEN"),  # optional
            "hf_repo_id": f"Kush210/{project_name}",  # optional
        },
        destination=f"{model.owner}/{model.name}",
    )

    # Store training ID in Firestore
    db = firestore.Client(database="photo-agent-users")
    job_ref = (
        db.collection("users")
        .document(user_id)
        .collection("training_jobs")
        .document(project_label)
    )
    job_ref.update(
        {"training_status": training.status, "replicate_training_id": training.id}
    )

    return {"message": "Training started", "training_id": training.id}


def check_training_status(user_id, project_label):
    """Checks the current training progress from Replicate API and stores the trained model."""

    replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_KEY"))
    db = firestore.Client(database="photo-agent-users")
    job_ref = (
        db.collection("users")
        .document(user_id)
        .collection("training_jobs")
        .document(project_label)
    )
    job = job_ref.get()

    if not job.exists:
        return "pending", None

    job_data = job.to_dict()
    training_id = job_data.get("replicate_training_id")

    if not training_id:
        return "pending", None

    try:
        training = replicate_client.trainings.get(training_id)

        if training.status == "succeeded":

            trained_model_url = training.output.get("version", "")

            # Save trained model URL in Firestore
            job_ref.update({"trained_model_url": trained_model_url})

            return "completed", trained_model_url

        return training.status, None
    except Exception as e:
        logger.error(f"Error checking training status: {e}")
        return "error", None
