"""Cloud Firestore access for saved ClipContext artifacts.

Centralizes all Firestore reads/writes for this feature so route handlers
stay thin (src/api/artifact_routes.py) and the AI pipeline itself has zero
Firestore dependency — persistence is purely an application/API-layer
concern, not a pipeline one.

Every method takes a verified Firebase uid and scopes all reads/writes to
users/{uid}/artifacts/... — there is no code path here that can read or
write another user's documents, since the path itself is derived from the
authenticated uid, never from client-supplied identifiers.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.artifacts.schemas import (
    ArtifactSelection,
    ArtifactSummary,
    ArtifactVideoInfo,
    SavedArtifact,
    SavedYouTubeUploadMetadata,
)
from src.models.discriminator.discriminator import DiscriminatorResult
from src.models.generated_content import GeneratedContent
from src.pipeline.schemas import VideoContextSummary

logger = logging.getLogger(__name__)


class ArtifactRepositoryError(RuntimeError):
    """Raised when a Firestore operation fails; callers translate to a 502."""


class ArtifactRepository:
    def __init__(self, client) -> None:
        self._client = client

    def _collection(self, uid: str):
        return self._client.collection("users").document(uid).collection("artifacts")

    def find_by_source_job(self, uid: str, job_id: str):
        try:
            query = self._collection(uid).where("source_job_id", "==", job_id).limit(1)
            docs = list(query.stream())
        except Exception as exc:
            raise ArtifactRepositoryError(str(exc)) from exc

        return docs[0] if docs else None

    def upsert_by_source_job(
        self,
        uid: str,
        job_id: str,
        video_context: VideoContextSummary,
        generated_content: GeneratedContent,
        rankings: DiscriminatorResult,
        selection: dict,
        video_display_name: Optional[str],
        youtube_upload: dict,
    ) -> SavedArtifact:
        now = datetime.now(timezone.utc)

        try:
            existing_doc = self.find_by_source_job(uid, job_id)

            body = {
                "source_job_id": job_id,
                "updated_at": now,
                "video": {
                    "original_filename": None,
                    "display_name": video_display_name,
                },
                "video_context": video_context.model_dump(),
                "generated_content": generated_content.model_dump(),
                "rankings": rankings.model_dump(),
                "selection": selection,
                "youtube_upload": youtube_upload,
            }

            if existing_doc is not None:
                artifact_id = existing_doc.id
                existing_data = existing_doc.to_dict() or {}
                created_at = existing_data.get("created_at") or now
                existing_doc.reference.set(body, merge=True)
            else:
                artifact_id = uuid.uuid4().hex
                created_at = now
                body["created_at"] = created_at
                self._collection(uid).document(artifact_id).set(body)

        except ArtifactRepositoryError:
            raise
        except Exception as exc:
            raise ArtifactRepositoryError(str(exc)) from exc

        return SavedArtifact(
            artifact_id=artifact_id,
            source_job_id=job_id,
            created_at=created_at,
            updated_at=now,
            video=ArtifactVideoInfo(display_name=video_display_name),
            video_context=video_context,
            generated_content=generated_content,
            rankings=rankings,
            selection=ArtifactSelection(**selection),
            youtube_upload=SavedYouTubeUploadMetadata(**youtube_upload),
        )

    def list_artifacts(self, uid: str) -> list[ArtifactSummary]:
        from firebase_admin import firestore

        try:
            query = self._collection(uid).order_by(
                "created_at", direction=firestore.Query.DESCENDING
            )
            docs = list(query.stream())
        except Exception as exc:
            raise ArtifactRepositoryError(str(exc)) from exc

        summaries: list[ArtifactSummary] = []

        for doc in docs:
            data = doc.to_dict() or {}

            try:
                titles = data.get("generated_content", {}).get("titles", [])
                selection = data.get("selection", {})
                selected_title_id = selection.get("title_id")
                selected_title_text = next(
                    (t.get("text", "") for t in titles if t.get("id") == selected_title_id),
                    "",
                )

                summaries.append(
                    ArtifactSummary(
                        artifact_id=doc.id,
                        created_at=data["created_at"],
                        topic=data.get("video_context", {}).get("topic", ""),
                        content_type=data.get("video_context", {}).get("content_type", ""),
                        selected_title=selected_title_text,
                        youtube_uploaded=bool(
                            data.get("youtube_upload", {}).get("uploaded", False)
                        ),
                    )
                )
            except Exception:
                logger.exception("Skipping malformed artifact doc id=%s", doc.id)
                continue

        return summaries

    def get_artifact(self, uid: str, artifact_id: str) -> Optional[SavedArtifact]:
        try:
            doc = self._collection(uid).document(artifact_id).get()
        except Exception as exc:
            raise ArtifactRepositoryError(str(exc)) from exc

        if not doc.exists:
            return None

        data = doc.to_dict() or {}

        try:
            return SavedArtifact(
                artifact_id=doc.id,
                source_job_id=data["source_job_id"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                video=ArtifactVideoInfo(**data.get("video", {})),
                video_context=VideoContextSummary(**data["video_context"]),
                generated_content=GeneratedContent(**data["generated_content"]),
                rankings=DiscriminatorResult(**data["rankings"]),
                selection=ArtifactSelection(**data["selection"]),
                youtube_upload=SavedYouTubeUploadMetadata(**data.get("youtube_upload", {})),
            )
        except Exception as exc:
            logger.exception("Malformed artifact doc uid=%s artifact_id=%s", uid, artifact_id)
            raise ArtifactRepositoryError(f"Malformed artifact data: {exc}") from exc

    def delete_artifact(self, uid: str, artifact_id: str) -> bool:
        try:
            doc_ref = self._collection(uid).document(artifact_id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            doc_ref.delete()
            return True
        except Exception as exc:
            raise ArtifactRepositoryError(str(exc)) from exc
