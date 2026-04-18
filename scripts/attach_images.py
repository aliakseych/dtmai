"""
Attach source images to questions interactively.

For each question without an image_url, shows the question text + source,
prompts for a local image path, uploads it to MinIO, and stores the public URL.

Usage:
    python -m scripts.attach_images              # only questions missing image_url
    python -m scripts.attach_images --all        # include already-attached questions
    python -m scripts.attach_images --subject MATH

Controls:
    <path>    — upload image and attach
    Enter     — skip this question
    q         — quit
"""
import asyncio
import json
import mimetypes
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from minio import Minio
from minio.commonconfig import ENABLED
from minio.lifecycleconfig import LifecycleConfig
from minio.error import S3Error

from src.interfaces.mongodb.client import MongoClient
from src.interfaces.mongodb.repositories.categories import CategoryRepository
from src.interfaces.mongodb.repositories.sources import SourceRepository
from src.settings import settings


# ── MinIO helpers ─────────────────────────────────────────────────────────────

def _build_minio_client() -> Minio:
    parsed = urlparse(settings.MINIO_URL)
    endpoint = parsed.netloc or parsed.path  # strip protocol
    secure = parsed.scheme == "https"
    return Minio(
        endpoint,
        access_key=settings.MINIO_USERNAME,
        secret_key=settings.MINIO_PASSWORD,
        secure=secure,
    )


def _ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"Created bucket: {bucket}")

    policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{bucket}/*"],
        }],
    })
    client.set_bucket_policy(bucket, policy)
    print(f"Public-read policy applied to bucket: {bucket}")


def _upload(client: Minio, bucket: str, question_id: str, image_path: Path) -> str:
    ext = image_path.suffix.lower()
    object_name = f"{question_id}{ext}"
    content_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"

    client.fput_object(bucket, object_name, str(image_path), content_type=content_type)

    base = settings.MINIO_PUBLIC_URL.rstrip("/")
    return f"{base}/{bucket}/{object_name}"


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    args = sys.argv[1:]
    include_all = "--all" in args
    subject_filter = None
    if "--subject" in args:
        idx = args.index("--subject")
        subject_filter = args[idx + 1].upper() if idx + 1 < len(args) else None

    if not settings.MINIO_PUBLIC_URL:
        print("Error: MINIO_PUBLIC_URL is not set in .env")
        sys.exit(1)

    minio_client = _build_minio_client()
    _ensure_bucket(minio_client, settings.MINIO_BUCKET)

    mongo = MongoClient(settings.MONGO_URI, settings.MONGO_DB_NAME)
    cat_repo = CategoryRepository(mongo)
    src_repo = SourceRepository(mongo)

    query: dict = {}
    if not include_all:
        query["image_url"] = {"$exists": False}
    if subject_filter:
        query["subject"] = subject_filter

    collection = mongo.questions()
    total = await collection.count_documents(query)
    if total == 0:
        print("No questions match the filter.")
        return

    print(f"\nFound {total} question(s). Controls: <path> = attach | Enter = skip | q = quit\n")

    # Pre-load category and source name caches
    all_cats = {c["id"]: c["name"] for c in await cat_repo.get_all()}
    all_sources = {s["id"]: s["name"] for s in await src_repo.get_all()}

    done = skipped = 0
    cursor = collection.find(query).sort("subject", 1)

    async for doc in cursor:
        question_id = str(doc["_id"])
        subject = doc.get("subject", "?")
        cat_name = all_cats.get(doc.get("category_id", ""), "—")
        question_text = doc.get("question", "")
        current_url = doc.get("image_url", "")
        source_name = all_sources.get(doc.get("source_id", ""), doc.get("source_id", "?"))

        print("─" * 60)
        print(f"[{done + skipped + 1}/{total}]  {subject}  ›  {cat_name}  ({source_name})")
        if current_url:
            print(f"  Current image: {current_url}")
        preview = question_text[:200].replace("\n", " ")
        print(f"  {preview}{'…' if len(question_text) > 200 else ''}\n")

        raw = input("  Image path: ").strip()

        if raw.lower() == "q":
            print("\nQuitting.")
            break

        if not raw:
            skipped += 1
            continue

        image_path = Path(raw).expanduser()
        if not image_path.exists():
            print(f"  ✗ File not found: {image_path}")
            skipped += 1
            continue

        try:
            url = _upload(minio_client, settings.MINIO_BUCKET, question_id, image_path)
            await collection.update_one({"_id": doc["_id"]}, {"$set": {"image_url": url}})
            print(f"  ✓ Uploaded → {url}")
            done += 1
        except S3Error as e:
            print(f"  ✗ MinIO error: {e}")
            skipped += 1

    print(f"\nDone. Attached: {done}  Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(main())