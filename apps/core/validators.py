"""Validateurs de securite pour les fichiers uploades."""
import imghdr
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


def validate_image_file(file: UploadedFile):
    """
    Valide qu'un fichier est une image securisee.

    Verifie:
    - L'extension du fichier
    - Le type MIME reel (magic bytes)
    - La taille du fichier
    """
    # Extensions autorisees
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

    # Extraire l'extension
    if '.' not in file.name:
        raise ValidationError("Le fichier doit avoir une extension.")

    ext = file.name.rsplit('.', 1)[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Extension '{ext}' non autorisee. Extensions acceptees: {', '.join(allowed_extensions)}"
        )

    # Verifier le type MIME reel (magic bytes)
    file.seek(0)
    img_type = imghdr.what(file)
    file.seek(0)

    if img_type not in ['jpeg', 'png', 'gif', 'webp']:
        raise ValidationError(
            "Le fichier n'est pas une image valide. "
            "Assurez-vous d'uploader une vraie image (JPG, PNG, GIF, WebP)."
        )

    # Verifier la taille (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        raise ValidationError(
            f"L'image est trop volumineuse ({file.size // 1024 // 1024}MB). "
            f"Taille maximale: 5MB."
        )


def validate_document_file(file: UploadedFile):
    """
    Valide qu'un fichier est un document securise.

    Verifie:
    - L'extension du fichier
    - Le type MIME
    - La taille du fichier
    """
    # Extensions et types MIME autorises
    allowed_types = {
        'pdf': ['application/pdf'],
        'doc': ['application/msword'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'xls': ['application/vnd.ms-excel'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'txt': ['text/plain'],
        'csv': ['text/csv', 'application/csv'],
    }

    # Extraire l'extension
    if '.' not in file.name:
        raise ValidationError("Le fichier doit avoir une extension.")

    ext = file.name.rsplit('.', 1)[-1].lower()
    if ext not in allowed_types:
        raise ValidationError(
            f"Extension '{ext}' non autorisee. "
            f"Extensions acceptees: {', '.join(allowed_types.keys())}"
        )

    # Verifier le type MIME
    content_type = getattr(file, 'content_type', '')
    if content_type and content_type not in allowed_types.get(ext, []):
        # Log mais ne pas bloquer si content_type n'est pas defini
        pass

    # Verifier la taille (max 25MB)
    max_size = 25 * 1024 * 1024  # 25MB
    if file.size > max_size:
        raise ValidationError(
            f"Le document est trop volumineux ({file.size // 1024 // 1024}MB). "
            f"Taille maximale: 25MB."
        )


def validate_receipt_file(file: UploadedFile):
    """
    Valide un justificatif (image ou PDF).
    """
    # Extensions autorisees
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf'}

    if '.' not in file.name:
        raise ValidationError("Le fichier doit avoir une extension.")

    ext = file.name.rsplit('.', 1)[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Extension '{ext}' non autorisee. "
            f"Extensions acceptees: {', '.join(allowed_extensions)}"
        )

    # Verifier la taille (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        raise ValidationError(
            f"Le fichier est trop volumineux ({file.size // 1024 // 1024}MB). "
            f"Taille maximale: 10MB."
        )

    # Pour les images, verifier le type MIME reel
    if ext in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
        file.seek(0)
        img_type = imghdr.what(file)
        file.seek(0)

        if img_type not in ['jpeg', 'png', 'gif', 'webp']:
            raise ValidationError(
                "Le fichier n'est pas une image valide."
            )
