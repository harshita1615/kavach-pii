"""Sentence templates. {SLOT}s are filled by build.py.

Labeled slots (become gold entities):
  AADHAAR PAN UPI IFSC BANK PHONE GSTIN EMAIL EMAIL_UPILIKE
Filler slots (never labeled):
  NAME CITY DATE BANKNAME and NEG_* hard negatives that look like PII but are not.

Some templates deliberately have no context words, to measure recall when the
surrounding text gives no hint.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    scenario: str  # support_chat | kyc | loan | bank_complaint | customer_service | system
    lang: str  # en | hinglish | hi
    text: str


POSITIVE = [
    # --- English ---------------------------------------------------------------
    Template(
        "support_chat",
        "en",
        "Hi, I need help with my refund. My PAN is {PAN} and the UPI ID is {UPI}.",
    ),
    Template("support_chat", "en", "Please update my mobile number to {PHONE} on my account."),
    Template(
        "support_chat", "en", "Can you send the refund to {UPI}? The amount was {NEG_AMOUNT}."
    ),
    Template(
        "support_chat",
        "en",
        "Order {NEG_ORDER12} was delivered but the refund to {UPI} has not arrived.",
    ),
    Template("support_chat", "en", "Please call me back on {PHONE}, my order no is {NEG_ORDER10}."),
    Template("support_chat", "en", "Don't send it to {UPI}; my email is {EMAIL_UPILIKE}."),
    Template(
        "kyc", "en", "KYC details - Name: {NAME}, Aadhaar: {AADHAAR}, PAN: {PAN}, Mobile: {PHONE}"
    ),
    Template("kyc", "en", "My aadhaar card number is {AADHAAR} and it is linked to {PHONE}."),
    Template("kyc", "en", "Uploading documents for {NAME}: PAN card {PAN}, Aadhaar {AADHAAR}."),
    Template("kyc", "en", "UID {AADHAAR} verification failed, please retry with OTP {NEG_OTP}."),
    Template(
        "loan",
        "en",
        "Loan application for {NAME} from {CITY}. PAN {PAN}, salary account {BANK} with IFSC {IFSC}.",
    ),
    Template("loan", "en", "Applicant mobile {PHONE}, email {EMAIL}, PAN {PAN}."),
    Template(
        "loan", "en", "Please disburse the loan to a/c no. {BANK} at {BANKNAME}, IFSC {IFSC}."
    ),
    Template(
        "bank_complaint",
        "en",
        "I was charged twice, UTR {NEG_UTR}. Refund to account number {BANK}, IFSC {IFSC}.",
    ),
    Template(
        "bank_complaint",
        "en",
        "Beneficiary: {NAME}, A/c No: {BANK}, IFSC: {IFSC}, Bank: {BANKNAME}.",
    ),
    Template(
        "bank_complaint", "en", "NEFT to {BANK} failed on {DATE}. Card {NEG_CARD} was not charged."
    ),
    Template(
        "bank_complaint",
        "en",
        "My savings account {BANK} was debited {NEG_AMOUNT} without consent.",
    ),
    Template(
        "customer_service",
        "en",
        "Our company GSTIN is {GSTIN}; please send invoice {NEG_INVOICE} to {EMAIL}.",
    ),
    Template(
        "customer_service", "en", "Contact {NAME} at {PHONE} or {EMAIL} for the verification visit."
    ),
    Template(
        "customer_service",
        "en",
        "Vendor GSTIN {GSTIN}, PAN {PAN}, payment via NEFT to {BANK} ({IFSC}).",
    ),
    Template(
        "customer_service", "en", "Customer {NAME} ({EMAIL}) reported an issue with PNR {NEG_PNR}."
    ),
    Template("customer_service", "en", "{NAME}, {CITY} - {NEG_PINCODE}. Phone: {PHONE}"),
    Template("customer_service", "en", "Please write to {EMAIL} with your GST number {GSTIN}."),
    # No context words at all.
    Template("customer_service", "en", "{NAME} | {PHONE} | {EMAIL} | {PAN}"),
    Template("customer_service", "en", "Details: {AADHAAR}, {PAN}, {UPI}"),
    Template("support_chat", "en", "Forwarding this: {PHONE}"),
    Template("customer_service", "en", "{GSTIN} / {IFSC} / {NAME}"),
    Template("support_chat", "en", "here it is {AADHAAR}"),
    Template("support_chat", "en", "{BANK} {IFSC} {NAME}"),
    # --- Hinglish ----------------------------------------------------------------
    Template("support_chat", "hinglish", "Mera PAN number {PAN} hai, refund {UPI} pe bhej do."),
    Template("kyc", "hinglish", "Bhaiya mera aadhaar {AADHAAR} hai aur mobile {PHONE}."),
    Template(
        "bank_complaint",
        "hinglish",
        "Mera khata number {BANK} hai, IFSC {IFSC}. Paise jaldi bhejo.",
    ),
    Template(
        "loan",
        "hinglish",
        "Loan ke liye PAN {PAN} aur aadhaar {AADHAAR} de diya tha, status kya hai?",
    ),
    Template("support_chat", "hinglish", "Mujhe {PHONE} pe call karo, ya {EMAIL} pe mail karo."),
    Template("customer_service", "hinglish", "Hamari dukaan ka GST number {GSTIN} hai."),
    Template("support_chat", "hinglish", "Paytm pe bhejo {UPI}, order {NEG_ORDER12} ka refund."),
    Template("support_chat", "hinglish", "Yeh mera naya number hai {PHONE}, purana band ho gaya."),
    Template(
        "bank_complaint",
        "hinglish",
        "Account {BANK} mein salary nahi aayi is mahine, IFSC {IFSC} hai.",
    ),
    Template(
        "bank_complaint",
        "hinglish",
        "Sir maine {NEG_AMOUNT} transfer kiye the UTR {NEG_UTR}, mere a/c {BANK} mein wapas karo.",
    ),
    Template("kyc", "hinglish", "aadhar {AADHAAR} pan {PAN} bas yahi hai mere paas"),
    Template("support_chat", "hinglish", "upi id {UPI} hai meri, wahi pe bhejna"),
    Template("support_chat", "hinglish", "{NAME} ji ka number {PHONE} hai, unse baat karo."),
    # --- Hindi (Devanagari) ------------------------------------------------------
    Template("kyc", "hi", "मेरा आधार नंबर {AADHAAR} है।"),
    Template("kyc", "hi", "मेरा पैन कार्ड नंबर {PAN} है और मोबाइल {PHONE} है।"),
    Template("bank_complaint", "hi", "कृपया पैसे मेरे खाते {BANK} में भेजें, IFSC कोड {IFSC} है।"),
    Template("support_chat", "hi", "मेरी यूपीआई आईडी {UPI} है।"),
    Template("customer_service", "hi", "हमारा जीएसटी नंबर {GSTIN} है।"),
    Template("support_chat", "hi", "मुझे {PHONE} पर फ़ोन करें या {EMAIL} पर ईमेल करें।"),
    Template("bank_complaint", "hi", "शिकायत: खाता संख्या {BANK} से {NEG_AMOUNT} कट गए।"),
    Template("loan", "hi", "लोन के लिए आवेदक {NAME}, पैन {PAN}, बैंक खाता {BANK}।"),
]

NEGATIVE = [
    Template(
        "system", "en", "Your order {NEG_ORDER12} has been shipped. Tracking ID {NEG_TRACKING}."
    ),
    Template("system", "en", "Invoice {NEG_INVOICE} for {NEG_AMOUNT} is due on {DATE}."),
    Template("system", "en", "Log entry {NEG_TIMESTAMP}: payment gateway timeout."),
    Template("system", "en", "PNR {NEG_PNR} confirmed for {NAME}."),
    Template("system", "en", "Your OTP is {NEG_OTP}. Do not share it with anyone."),
    Template("system", "en", "Card ending {NEG_CARD} was charged {NEG_AMOUNT}."),
    Template("support_chat", "en", "Ticket #{NEG_TICKET} raised by {NAME} from {CITY}."),
    Template("support_chat", "en", "Order no. {NEG_ORDER10} cannot be cancelled now."),
    Template("support_chat", "en", "Reference {NEG_BADPAN} does not match our records."),
    Template("kyc", "en", "The number {NEG_BADAADHAAR} you entered is not valid."),
    Template("system", "en", "Transaction {NEG_UTR} successful at {DATE}."),
    Template("system", "en", "Batch {NEG_TIMESTAMP} processed {NEG_SMALL} records."),
    Template("customer_service", "en", "Meeting moved to {DATE}, room 402, extension 2231."),
    Template("customer_service", "en", "Thanks {NAME}, we will get back to you within 48 hours."),
    Template("support_chat", "hinglish", "Mera order {NEG_ORDER12} abhi tak nahi aaya."),
    Template("support_chat", "hinglish", "Pincode {NEG_PINCODE} mein delivery available hai kya?"),
    Template("support_chat", "hinglish", "Order {NEG_ORDER10} ka status batao please."),
    Template(
        "support_chat", "hinglish", "Bill number {NEG_INVOICE} ka payment {NEG_AMOUNT} ho gaya."
    ),
    Template("system", "hi", "आपका ऑर्डर {NEG_ORDER12} भेज दिया गया है।"),
    Template("system", "hi", "आपका ओटीपी {NEG_OTP} है।"),
]

# --- Held-out split -------------------------------------------------------------
# Written after Kavach was tuned on the templates above, and never used for
# tuning. Different phrasing: chat abbreviations, numbers with no label directly
# before them, values at sentence starts, multi-sentence messages.

HOLDOUT_POSITIVE = [
    Template("kyc", "en", "pls verify kyc asap. aadhar no - {AADHAAR}"),
    Template("support_chat", "en", "can u chk my acct {BANK} pls, money not credited"),
    Template("support_chat", "en", "sbi ifsc {IFSC} and the acc is {BANK}"),
    Template("support_chat", "en", "phonepe: {UPI}"),
    Template("support_chat", "en", "my num {PHONE}, whatsapp only"),
    Template("customer_service", "en", "Name: {NAME}; DOB: {DATE}; PAN: {PAN}; City: {CITY}"),
    Template("customer_service", "en", "gst - {GSTIN}, billing email {EMAIL}"),
    Template("support_chat", "en", "{PHONE} is my alternate number in case I don't pick up."),
    Template("support_chat", "en", "I've paid from {UPI} twice. Please reverse one."),
    Template("loan", "en", "Co-applicant {NAME}. Her PAN: {PAN}. Her mobile: {PHONE}."),
    Template(
        "bank_complaint", "en", "Sent {NEG_AMOUNT} to beneficiary account {BANK} but it bounced."
    ),
    Template("kyc", "en", "The Aadhaar on file is {AADHAAR}, the one on my new card is {AADHAAR}."),
    Template("customer_service", "en", "Escalating: customer reachable at {PHONE} / {EMAIL}."),
    Template(
        "loan", "en", "Salary credited to {BANK} ({BANKNAME}, branch IFSC {IFSC}) every month."
    ),
    Template("customer_service", "en", "Supplier: {NAME}, GSTIN {GSTIN}, contact {PHONE}"),
    Template("support_chat", "en", "{EMAIL}"),
    Template("support_chat", "en", "{UPI}"),
    Template("support_chat", "en", "pan {PAN}"),
    Template("support_chat", "en", "Copying from my passbook: {BANK}"),
    Template("support_chat", "hinglish", "bhai {UPI} pe 500 bhej de"),
    Template("kyc", "hinglish", "mera aadhar card ka no {AADHAAR} h"),
    Template("bank_complaint", "hinglish", "khate me paise nahi aaye, khata no {BANK}"),
    Template("support_chat", "hinglish", "number note karlo {PHONE}"),
    Template("customer_service", "hinglish", "humara gstin {GSTIN} hai, bill isi pe banana"),
    Template("loan", "hinglish", "PAN {PAN} hai, CIBIL check karke batao"),
    Template("support_chat", "hinglish", "mail kar dena {EMAIL} pe"),
    Template("kyc", "hi", "आधार कार्ड {AADHAAR} और पैन {PAN} जमा कर दिया है।"),
    Template("support_chat", "hi", "मेरा नंबर {PHONE} है, कॉल करें।"),
    Template("bank_complaint", "hi", "खाता {BANK} में पैसा नहीं आया।"),
    Template("support_chat", "hi", "{UPI} पर भुगतान करें।"),
]

HOLDOUT_NEGATIVE = [
    Template("system", "en", "Your parcel {NEG_ORDER12} is out for delivery."),
    Template("support_chat", "en", "The code {NEG_ORDER10} didn't work at checkout."),
    Template("system", "en", "Confirmation {NEG_PNR} for 2 adults, check-in {DATE}."),
    Template("system", "en", "Files {NEG_ORDER12} and {NEG_ORDER12} were archived."),
    Template("system", "en", "Job started at {NEG_TIMESTAMP} and finished in 42s."),
    Template("support_chat", "en", "I got charged {NEG_AMOUNT} for item {NEG_ORDER10}."),
    Template("support_chat", "en", "Is {NEG_PINCODE} serviceable?"),
    Template("support_chat", "en", "Please quote {NEG_INVOICE} in all replies."),
    Template("kyc", "en", "That ID ({NEG_BADAADHAAR}) was rejected by the system."),
    Template("kyc", "en", "Code {NEG_BADPAN} is not a PAN, it's our internal reference."),
    Template("system", "en", "Device serial {NEG_TRACKING}, firmware {NEG_SMALL}."),
    Template("support_chat", "hinglish", "parcel {NEG_ORDER12} kab tak aayega?"),
    Template("support_chat", "hinglish", "{NEG_ORDER10} wala item damaged tha"),
    Template("system", "hi", "पार्सल {NEG_ORDER12} रास्ते में है।"),
    Template("support_chat", "en", "Thanks, {NAME}! Talk soon."),
]
