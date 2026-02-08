"""
Agent version information.
"""

__version__ = "1.0.0"
__git_commit__ = "unknown"
__build_date__ = "unknown"


def get_version() -> str:
    """Get agent version string."""
    return __version__


def get_full_version() -> dict:
    """Get full version information."""
    return {
        "version": __version__,
        "git_commit": __git_commit__,
        "build_date": __build_date__,
    }
