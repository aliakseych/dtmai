"""
Attach source images to questions interactively.

For each question without an image_url, shows the question text + source,
prompts for a local image path, uploads it to RustFS, and stores the public URL.

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

sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
from botocore.exceptions import ClientError

from src.interfaces.mongodb.client import MongoClient
from src.interfaces.mongodb.repositories.categories import CategoryRepository
from src.interfaces.mongodb.repositories.sources import SourceRepository
from src.settings import settings


# ── RustFS helpers ────────────────────────────────────────────────────────────

def _build_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )


def _ensure_bucket(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
            client.create_bucket(Bucket=bucket)
            print(f"Created bucket: {bucket}")
        else:
            raise

    policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{bucket}/*"],
        }],
    })
    client.put_bucket_policy(Bucket=bucket, Policy=policy)
    print(f"Public-read policy applied to bucket: {bucket}")


def _upload(client, bucket: str, question_id: str, image_path: Path) -> str:
    ext = image_path.suffix.lower()
    object_name = f"{question_id}{ext}"
    content_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"

    client.upload_file(
        str(image_path),
        bucket,
        object_name,
        ExtraArgs={"ContentType": content_type},
    )

    base = settings.S3_PUBLIC_URL.rstrip("/")
    return f"{base}/{bucket}/{object_name}"


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    args = sys.argv[1:]
    include_all = "--all" in args
    subject_filter = None
    if "--subject" in args:
        idx = args.index("--subject")
        subject_filter = args[idx + 1].upper() if idx + 1 < len(args) else None

    if not settings.S3_PUBLIC_URL:
        print("Error: S3_PUBLIC_URL is not set in .env")
        sys.exit(1)

    s3_client = _build_s3_client()
    _ensure_bucket(s3_client, settings.S3_BUCKET)

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
            url = _upload(s3_client, settings.S3_BUCKET, question_id, image_path)
            await collection.update_one({"_id": doc["_id"]}, {"$set": {"image_url": url}})
            print(f"  ✓ Uploaded → {url}")
            done += 1
        except ClientError as e:
            print(f"  ✗ S3 error: {e}")
            skipped += 1

    print(f"\nDone. Attached: {done}  Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
