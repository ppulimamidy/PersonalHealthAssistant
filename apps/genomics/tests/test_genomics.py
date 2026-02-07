"""Unit tests for Genomics service models."""
import pytest
from datetime import datetime
import uuid


class TestGenomicDataModels:
    def test_genomic_data_create(self):
        """Test GenomicDataCreate model with valid data."""
        from apps.genomics.models.genomic_data import GenomicDataCreate

        data = GenomicDataCreate(
            data_source="clinical_lab",
            data_format="vcf",
            file_path="/data/genomics/sample_001.vcf",
            file_size=1024000,
            checksum="abc123hash",
            sample_id="SAMPLE-001",
            collection_date=datetime.utcnow(),
            lab_name="GenomeLab",
            test_name="Whole Genome Sequencing",
        )
        assert data.data_source == "clinical_lab"
        assert data.data_format == "vcf"
        assert data.file_path == "/data/genomics/sample_001.vcf"
        assert data.sample_id == "SAMPLE-001"

    def test_genomic_data_create_minimal(self):
        """Test GenomicDataCreate with minimal required fields."""
        from apps.genomics.models.genomic_data import GenomicDataCreate

        data = GenomicDataCreate(
            data_source="direct_to_consumer",
            data_format="json",
            file_path="/data/genomics/sample.json",
        )
        assert data.lab_name is None
        assert data.extra_metadata == {}

    def test_genomic_data_update(self):
        """Test GenomicDataUpdate allows partial updates."""
        from apps.genomics.models.genomic_data import GenomicDataUpdate

        update = GenomicDataUpdate(
            quality_score=0.95,
            quality_status="excellent",
            is_processed=True,
        )
        assert update.quality_score == 0.95
        assert update.is_analyzed is None

    def test_genomic_data_missing_required(self):
        """Test GenomicDataCreate fails without required fields."""
        from apps.genomics.models.genomic_data import GenomicDataCreate

        with pytest.raises(Exception):
            GenomicDataCreate(data_source="clinical_lab")


class TestGeneticVariantModels:
    def test_variant_create(self):
        """Test GeneticVariantCreate model with valid data."""
        from apps.genomics.models.genomic_data import GeneticVariantCreate

        variant = GeneticVariantCreate(
            genomic_data_id=uuid.uuid4(),
            chromosome="17",
            position=7577120,
            reference_allele="C",
            alternate_allele="T",
            variant_type="snv",
            rs_id="rs28934578",
            gene_name="TP53",
            clinical_significance="pathogenic",
            quality_score=99.0,
            read_depth=50,
        )
        assert variant.chromosome == "17"
        assert variant.gene_name == "TP53"
        assert variant.variant_type == "snv"
        assert variant.clinical_significance == "pathogenic"

    def test_variant_create_minimal(self):
        """Test GeneticVariantCreate with minimal fields."""
        from apps.genomics.models.genomic_data import GeneticVariantCreate

        variant = GeneticVariantCreate(
            genomic_data_id=uuid.uuid4(),
            chromosome="1",
            position=100000,
            reference_allele="A",
            alternate_allele="G",
            variant_type="snv",
        )
        assert variant.rs_id is None
        assert variant.gene_name is None
        assert variant.annotations == {}

    def test_variant_missing_required(self):
        """Test GeneticVariantCreate fails without required fields."""
        from apps.genomics.models.genomic_data import GeneticVariantCreate

        with pytest.raises(Exception):
            GeneticVariantCreate(
                chromosome="1",
                position=100000,
                # Missing genomic_data_id, alleles, variant_type
            )


class TestPharmacogenomicModels:
    def test_pharmacogenomic_profile_create(self):
        """Test PharmacogenomicProfileCreate model."""
        from apps.genomics.models.genomic_data import PharmacogenomicProfileCreate

        profile = PharmacogenomicProfileCreate(
            profile_name="CYP2D6 Profile",
            test_date=datetime.utcnow(),
            lab_name="PharmaGenomics Lab",
            test_method="TaqMan Assay",
            gene_drug_interactions=[
                {"gene": "CYP2D6", "drug": "codeine", "effect": "poor_metabolizer"},
            ],
            metabolizer_status={"CYP2D6": "poor", "CYP2C19": "normal"},
        )
        assert profile.profile_name == "CYP2D6 Profile"
        assert len(profile.gene_drug_interactions) == 1
        assert profile.metabolizer_status["CYP2D6"] == "poor"

    def test_pharmacogenomic_missing_required(self):
        """Test PharmacogenomicProfileCreate fails without required fields."""
        from apps.genomics.models.genomic_data import PharmacogenomicProfileCreate

        with pytest.raises(Exception):
            PharmacogenomicProfileCreate(profile_name="Incomplete")


class TestGenomicEnums:
    def test_data_source_enum(self):
        """Test DataSource enum values."""
        from apps.genomics.models.genomic_data import DataSource

        assert DataSource.CLINICAL_LAB == "clinical_lab"
        assert DataSource.RESEARCH_STUDY == "research_study"

    def test_variant_type_enum(self):
        """Test VariantType enum values."""
        from apps.genomics.models.genomic_data import VariantType

        assert VariantType.SNV == "snv"
        assert VariantType.INDEL == "indel"
        assert VariantType.CNV == "cnv"

    def test_variant_classification_enum(self):
        """Test VariantClassification enum values."""
        from apps.genomics.models.genomic_data import VariantClassification

        assert VariantClassification.PATHOGENIC == "pathogenic"
        assert VariantClassification.BENIGN == "benign"
