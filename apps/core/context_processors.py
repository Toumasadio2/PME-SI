"""
Context processors for templates.
"""
from django.http import HttpRequest


def hex_to_rgb(hex_color: str) -> str:
    """Convert hex color to RGB values for CSS."""
    if not hex_color:
        return "59, 130, 246"  # Default blue

    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        if len(hex_color) != 6:
            return "59, 130, 246"  # Default if invalid length
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
    except (ValueError, TypeError):
        return "59, 130, 246"  # Default on any error


def generate_color_shades(hex_color: str) -> dict:
    """Generate color shades (50-900) from a base color."""
    # Default shades for blue (#3B82F6)
    default_shades = {
        50: "#eff6ff", 100: "#dbeafe", 200: "#bfdbfe", 300: "#93c5fd",
        400: "#60a5fa", 500: "#3b82f6", 600: "#2563eb", 700: "#1d4ed8",
        800: "#1e40af", 900: "#1e3a8a"
    }

    if not hex_color:
        return default_shades

    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        if len(hex_color) != 6:
            return default_shades

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        shades = {}
        # Generate lighter shades (50-400)
        for i, factor in enumerate([0.95, 0.9, 0.8, 0.7, 0.6]):
            shade_num = [50, 100, 200, 300, 400][i]
            new_r = int(r + (255 - r) * factor)
            new_g = int(g + (255 - g) * factor)
            new_b = int(b + (255 - b) * factor)
            shades[shade_num] = f"#{new_r:02x}{new_g:02x}{new_b:02x}"

        # Base color (500)
        shades[500] = f"#{hex_color}"

        # Generate darker shades (600-900)
        for i, factor in enumerate([0.85, 0.7, 0.55, 0.4]):
            shade_num = [600, 700, 800, 900][i]
            new_r = int(r * factor)
            new_g = int(g * factor)
            new_b = int(b * factor)
            shades[shade_num] = f"#{new_r:02x}{new_g:02x}{new_b:02x}"

        return shades
    except (ValueError, TypeError):
        return default_shades


def tenant_context(request: HttpRequest) -> dict:
    """Add tenant-related context to all templates."""
    # Default colors
    default_primary = "#3B82F6"
    default_secondary = "#1E40AF"

    context = {
        "current_organization": None,
        "organization_name": "",
        "organization_logo": None,
        "theme_primary": default_primary,
        "theme_secondary": default_secondary,
        "theme_primary_rgb": hex_to_rgb(default_primary),
        "theme_secondary_rgb": hex_to_rgb(default_secondary),
        "theme_primary_shades": generate_color_shades(default_primary),
        "theme_secondary_shades": generate_color_shades(default_secondary),
    }

    if hasattr(request, "organization") and request.organization:
        org = request.organization
        primary = org.primary_color or default_primary
        secondary = org.secondary_color or default_secondary

        # Safely get logo URL
        logo_url = None
        try:
            if org.logo and hasattr(org.logo, 'url'):
                logo_url = org.logo.url
        except (ValueError, AttributeError):
            pass

        context.update({
            "current_organization": org,
            "organization_name": org.name,
            "organization_logo": logo_url,
            "theme_primary": primary,
            "theme_secondary": secondary,
            "theme_primary_rgb": hex_to_rgb(primary),
            "theme_secondary_rgb": hex_to_rgb(secondary),
            "theme_primary_shades": generate_color_shades(primary),
            "theme_secondary_shades": generate_color_shades(secondary),
        })

    return context
