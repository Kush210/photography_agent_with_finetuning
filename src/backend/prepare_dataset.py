import os
import zipfile
from google.cloud import firestore, storage
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
#     "/home/kush_210/Vettura-genai/photography_agent_with_finetuning/service-account-key.json"
# )


def prepare_flux_dataset(user_id, project_label):
    """Fetches images & descriptions from Firestore, creates caption .txt files, zips, and uploads to GCP."""

    db = firestore.Client(database="photo-agent-users")
    storage_client = storage.Client()
    bucket_name = "flux-dev-training-datasets"
    dataset_bucket = storage_client.bucket(bucket_name)

    user_ref = db.collection("users").document(user_id)
    job_ref = user_ref.collection("training_jobs").document(project_label)
    job = job_ref.get()

    if not job.exists:
        return None, "Project not found"

    job_data = job.to_dict()
    images = job_data.get("images", {})

    # Create a temporary dataset folder
    dataset_folder = f"/tmp/{user_id}_{project_label}_dataset"
    os.makedirs(dataset_folder, exist_ok=True)

    dataset_zip = f"{dataset_folder}.zip"

    # Create text files for captions
    for category, image_list in images.items():
        for img in image_list:
            image_url = img["url"]
            description = (
                img["description"] if img["description"] else "No description available"
            )

            # Extract bucket name and blob path from GCS URL
            gcs_path_parts = image_url.replace(
                "https://storage.googleapis.com/", ""
            ).split("/", 1)
            bucket_name = gcs_path_parts[0]
            blob_path = gcs_path_parts[1]

            # Get the bucket and blob
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            # Extract image filename and create matching .txt filename
            file_name = os.path.basename(image_url)
            image_path = os.path.join(dataset_folder, file_name)
            txt_filename = os.path.splitext(file_name)[0] + ".txt"

            # Download image from GCS Storage
            try:
                blob.download_to_filename(image_path)
                # print(f"Downloaded: {file_name}")
            except Exception as e:
                print(f"Error downloading {file_name}: {e}")
                continue

            # Write caption to a corresponding .txt file
            with open(os.path.join(dataset_folder, txt_filename), "w") as txt_file:
                txt_file.write(description)

    # Zip the dataset folder
    with zipfile.ZipFile(dataset_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(dataset_folder):
            file_path = os.path.join(dataset_folder, file)
            zipf.write(file_path, os.path.basename(file_path))

    # Upload the dataset to GCP Storage
    blob = dataset_bucket.blob(os.path.basename(dataset_zip))
    blob.upload_from_filename(dataset_zip)
    blob.make_public()  # Ensure it is publicly accessible

    dataset_url = blob.public_url
    return dataset_url, None


# url, error = prepare_flux_dataset("Kush2101999@gmail.com", "yash-kush")

# if error:
#     print({"error": error})
# else:
#     print(url)
