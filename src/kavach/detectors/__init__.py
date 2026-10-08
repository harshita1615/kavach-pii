"""Entity detectors. Each finds and validates one entity type."""

from kavach.detectors.aadhaar import AadhaarDetector
from kavach.detectors.base import Detector
from kavach.detectors.pan import PanDetector

__all__ = ["AadhaarDetector", "Detector", "PanDetector"]
