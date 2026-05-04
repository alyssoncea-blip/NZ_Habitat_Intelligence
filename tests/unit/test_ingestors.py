"""Unit tests for bronze layer ingestors."""
import tempfile
from pathlib import Path



class TestWorldBankIngestor:
    """Tests for World Bank ingestor."""

    def test_ingestor_initialization(self):
        """Test that WorldBankIngestor can be initialized."""
        from data_pipeline.bronze.ingestors.world_bank_ingestor import WorldBankIngestor
        with tempfile.TemporaryDirectory() as tmpdir:
            ingestor = WorldBankIngestor(tmpdir)
            assert ingestor is not None
            assert ingestor.data_dir == Path(tmpdir)

    def test_ingestor_has_required_methods(self):
        """Test that ingestor has required methods."""
        from data_pipeline.bronze.ingestors.world_bank_ingestor import WorldBankIngestor
        with tempfile.TemporaryDirectory() as tmpdir:
            ingestor = WorldBankIngestor(tmpdir)
            assert hasattr(ingestor, "run_ingestion")
            assert callable(ingestor.run_ingestion)


class TestRBNZIngestor:
    """Tests for RBNZ ingestor."""

    def test_ingestor_initialization(self):
        """Test that RBNZIngestor can be initialized."""
        from data_pipeline.bronze.ingestors.rbnz_ingestor import RBNZIngestor
        with tempfile.TemporaryDirectory() as tmpdir:
            ingestor = RBNZIngestor(tmpdir)
            assert ingestor is not None

    def test_ingestor_has_required_methods(self):
        """Test that ingestor has required methods."""
        from data_pipeline.bronze.ingestors.rbnz_ingestor import RBNZIngestor
        with tempfile.TemporaryDirectory() as tmpdir:
            ingestor = RBNZIngestor(tmpdir)
            assert hasattr(ingestor, "run_ingestion")


class TestStatsNZIngestor:
    """Tests for Stats NZ ingestor."""

    def test_ingestor_initialization(self):
        """Test that StatsNZIngestor can be initialized."""
        from data_pipeline.bronze.ingestors.stats_nz_ingestor import StatsNZIngestor
        with tempfile.TemporaryDirectory() as tmpdir:
            ingestor = StatsNZIngestor(tmpdir)
            assert ingestor is not None


class TestMBIEIngestor:
    """Tests for MBIE tourism ingestor."""

    def test_ingestor_initialization(self):
        """Test that MBIEIngestor can be initialized."""
        from data_pipeline.bronze.ingestors.mbie_tourism_ingestor import MBIEIngestor
        with tempfile.TemporaryDirectory() as tmpdir:
            ingestor = MBIEIngestor(tmpdir)
            assert ingestor is not None


class TestLINZIngestor:
    """Tests for LINZ ingestor."""

    def test_ingestor_initialization(self):
        """Test that LINZIngestor can be initialized."""
        from data_pipeline.bronze.ingestors.linz_ingestor import LINZIngestor
        with tempfile.TemporaryDirectory() as tmpdir:
            ingestor = LINZIngestor(tmpdir)
            assert ingestor is not None


class TestREINZIngestor:
    """Tests for REINZ ingestor."""

    def test_ingestor_initialization(self):
        """Test that REINZIngestor can be initialized."""
        from data_pipeline.bronze.ingestors.reinz_ingestor import REINZIngestor
        with tempfile.TemporaryDirectory() as tmpdir:
            ingestor = REINZIngestor(tmpdir)
            assert ingestor is not None


class TestBronzeOrchestrator:
    """Tests for Bronze orchestrator."""

    def test_orchestrator_initialization(self):
        """Test that BronzeOrchestrator can be initialized."""
        from data_pipeline.bronze.bronze_orchestrator import BronzeOrchestrator
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = BronzeOrchestrator(data_dir=tmpdir)
            assert orchestrator is not None
            assert orchestrator.data_dir == Path(tmpdir)

    def test_orchestrator_has_ingestors(self):
        """Test that orchestrator has ingestors dictionary."""
        from data_pipeline.bronze.bronze_orchestrator import BronzeOrchestrator
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = BronzeOrchestrator(data_dir=tmpdir)
            assert hasattr(orchestrator, "ingestors")
            assert isinstance(orchestrator.ingestors, dict)

    def test_orchestrator_has_schedule(self):
        """Test that orchestrator has schedule configuration."""
        from data_pipeline.bronze.bronze_orchestrator import BronzeOrchestrator
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = BronzeOrchestrator(data_dir=tmpdir)
            assert hasattr(orchestrator, "schedule")
            assert "daily" in orchestrator.schedule
            assert "weekly" in orchestrator.schedule
            assert "monthly" in orchestrator.schedule

    def test_orchestrator_cache_operations(self):
        """Test cache load and save operations."""
        from data_pipeline.bronze.bronze_orchestrator import BronzeOrchestrator
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = BronzeOrchestrator(data_dir=tmpdir)
            orchestrator._cache = {"test": {"cached_at": "2026-01-01", "data": {}}}
            orchestrator._save_cache()
            assert orchestrator.cache_file.exists()
            orchestrator._load_cache()
            assert "test" in orchestrator._cache

    def test_orchestrator_check_data_freshness(self):
        """Test data freshness check."""
        from data_pipeline.bronze.bronze_orchestrator import BronzeOrchestrator
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = BronzeOrchestrator(data_dir=tmpdir)
            freshness = orchestrator.check_data_freshness()
            assert "sources" in freshness
            assert "overall_freshness_score" in freshness
