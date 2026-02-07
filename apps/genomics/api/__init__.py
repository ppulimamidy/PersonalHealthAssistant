"""
API endpoints for Genomics Service.

This module contains all the API routers for genomic analysis including:
- Genomic data management
- Analysis endpoints
- Variant detection
- Pharmacogenomics
- Ancestry analysis
- Genetic counseling
"""

from . import genomic_data, analysis, variants, pharmacogenomics, ancestry, counseling

__all__ = [
    "genomic_data",
    "analysis", 
    "variants",
    "pharmacogenomics",
    "ancestry",
    "counseling"
] 