#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# WeasyPrint: Configure library path for PDF generation on macOS
if sys.platform == 'darwin':
    homebrew_lib = '/opt/homebrew/lib'
    if os.path.exists(homebrew_lib):
        current = os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
        if homebrew_lib not in current:
            os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = f"{homebrew_lib}:{current}" if current else homebrew_lib


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
