"""Entity detectors. Each finds and validates one entity type."""

from kavach.detectors.aadhaar import AadhaarDetector
from kavach.detectors.bank import BankAccountDetector
from kavach.detectors.base import Detector
from kavach.detectors.email import EmailDetector
from kavach.detectors.gstin import GstinDetector
from kavach.detectors.ifsc import IfscDetector
from kavach.detectors.pan import PanDetector
from kavach.detectors.phone import PhoneDetector
from kavach.detectors.upi import UpiDetector

ALL_DETECTORS: tuple[type[Detector], ...] = (
    AadhaarDetector,
    PanDetector,
    UpiDetector,
    IfscDetector,
    BankAccountDetector,
    PhoneDetector,
    GstinDetector,
    EmailDetector,
)

__all__ = [
    "ALL_DETECTORS",
    "AadhaarDetector",
    "BankAccountDetector",
    "Detector",
    "EmailDetector",
    "GstinDetector",
    "IfscDetector",
    "PanDetector",
    "PhoneDetector",
    "UpiDetector",
]
