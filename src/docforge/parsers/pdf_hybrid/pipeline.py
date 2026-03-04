from docforge.connectors.models import RawDocument
from docforge.parsers.models import ParserConfig
from docforge.parsers.pdf_hybrid.schema import ExtractedPdfDocument


def run_pdf_pipeline(doc: RawDocument, config: ParserConfig) -> ExtractedPdfDocument:
    """
    Coordinates parallel engine execution and intermediate assembly.
    Stubbed until Phase 1 Component 3.2 is fully wired.
    """
    raise NotImplementedError("run_pdf_pipeline is not fully implemented yet.")
