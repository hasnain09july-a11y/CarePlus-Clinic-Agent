import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

BASE = Path(__file__).resolve().parent
CLINIC_FILE = BASE / "clinic_config.json"
REQUESTS_FILE = BASE / "appointment_requests.json"

DEFAULT_CLINIC = {
    "name": "CarePlus Clinic",
    "address": "Main Road, Karachi, Pakistan (demo address)",
    "phone": "0300-1234567 (demo number)",
    "hours": "Monday to Saturday, 9:00 AM to 6:00 PM",
    "fees": "Please contact the clinic for current fees.",
    "services": ["General consultation", "Routine checkups", "General health consultations"]
}
# Limited phrase detection only; this is NOT medical triage.
EMERGENCY_PHRASES = (
    "can't breathe", "cannot breathe", "difficulty breathing",
    "chest pain", "severe bleeding", "unconscious",
    "not responding", "severe allergic reaction"
)
APPOINTMENT_PHRASES = (
    "appointment", "book a visit", "book a doctor", "see a doctor",
    "visit the clinic", "schedule a visit", "make a booking",
    "request a visit", "consultation"
)

def read_json(path, fallback):
    if not path.exists():
        return fallback
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return fallback

def write_json(path, data):
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def load_clinic():
    data = read_json(CLINIC_FILE, {})
    clinic = DEFAULT_CLINIC.copy()
    if isinstance(data, dict):
        clinic.update(data)
    if not CLINIC_FILE.exists():
        write_json(CLINIC_FILE, clinic)
    return clinic

def normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def has_phrase(message, phrases):
    padded = f" {normalize(message)} "
    return any(f" {phrase} " in padded for phrase in phrases)

def is_yes(text):
    return normalize(text) in {"yes", "y", "yes please", "sure", "okay", "ok"}

def is_no(text):
    return normalize(text) in {"no", "n", "no thanks", "not now"}

class ClinicAssistant:
    def __init__(self, clinic=None, requests_file=REQUESTS_FILE):
        self.clinic = clinic or DEFAULT_CLINIC.copy()
        self.requests_file = Path(requests_file)
        self.state = "idle"
        self.pending = {}

    def save_request(self):
        records = read_json(self.requests_file, [])
        if not isinstance(records, list):
            return "Sorry, appointment records could not be read. Please contact clinic staff."
        record = {
            "request_id": str(uuid4()),
            "patient_name": self.pending["name"],
            "contact": self.pending["contact"],
            "preferred_date": self.pending["date"],
            "preferred_time": self.pending["time"],
            "status": "Pending clinic confirmation",
            "created_at": datetime.now().isoformat(timespec="seconds")
        }
        try:
            records.append(record)
            write_json(self.requests_file, records)
        except OSError:
            return "Sorry, I could not save the request. Please contact clinic staff."
        self.state = "idle"
        self.pending = {}
        return (
            "Your appointment request has been saved. "
            f"Reference: {record['request_id']}\\n"
            "This is NOT a confirmed appointment. Clinic staff must contact you "
            "to confirm availability."
        )

    def reply(self, message):
        message = message.strip()
        if not message:
            return "Please type a message so I can help."
        text = normalize(message)

        if text in {"cancel", "stop", "never mind", "nevermind"}:
            self.state, self.pending = "idle", {}
            return "Your request process has been cancelled. How else can I help?"

        if has_phrase(text, EMERGENCY_PHRASES):
            return (
                "Your message may describe a medical emergency. Please contact "
                "your local emergency service or go to the nearest emergency "
                "department now. Do not wait for an appointment or this chat."
            )

        if text in {"exit", "quit", "bye"}:
            self.state, self.pending = "idle", {}
            return f"Thank you for contacting {self.clinic['name']}. Goodbye!"

        if text == "help":
            return (
                "I can share clinic hours, address, contact details, fees and services, "
                "or help submit an appointment request. Type 'appointment' to start "
                "or 'cancel' to stop."
            )

        # Stateful appointment flow: each answer is used only for the current field.
        if self.state == "confirm":
            if is_yes(text):
                self.state = "name"
                return "What is the patient's name? Use fictional details while testing."
            if is_no(text):
                self.state = "idle"
                return "No problem. I have not created a request. How else can I help?"
            return "Would you like to submit an appointment request? Please answer yes or no."

        if self.state == "name":
            if len(message) < 2:
                return "Please enter a name with at least 2 characters, or type 'cancel'."
            self.pending["name"] = message[:80]
            self.state = "contact"
            return "What phone number or email should clinic staff use to contact you?"

        if self.state == "contact":
            if len(message) < 5 or len(message) > 120:
                return "Please enter a valid-looking phone number or email, or type 'cancel'."
            self.pending["contact"] = message
            self.state = "date"
            return "What date would you prefer? Example: 25 November 2026."

        if self.state == "date":
            if len(message) < 4 or len(message) > 50:
                return "Please enter a date in a readable format, or type 'cancel'."
            self.pending["date"] = message
            self.state = "time"
            return "What time would you prefer? Example: 10:30 AM."

        if self.state == "time":
            if len(message) < 2 or len(message) > 40:
                return "Please enter a preferred time, or type 'cancel'."
            self.pending["time"] = message
            return self.save_request()

        if has_phrase(text, ("hello", "hi", "hey", "good morning", "good afternoon", "good evening")):
            return (
                f"Hello! Welcome to {self.clinic['name']}. I can help with clinic "
                "information and appointment requests. What would you like to know?"
            )

        if has_phrase(text, APPOINTMENT_PHRASES):
            self.state = "confirm"
            return (
                "I can submit an appointment request. If this is an emergency, seek "
                "urgent medical care now. Would you like to continue? Please answer yes or no."
            )

        faq_terms = {
            "hours": ("hours", "timing", "open", "close"),
            "address": ("address", "location", "where are you", "where is the clinic"),
            "phone": ("phone", "contact", "number", "call"),
            "fees": ("fee", "fees", "price", "cost", "charges"),
            "services": ("service", "services", "checkup", "check-up")
        }
        for key, terms in faq_terms.items():
            if has_phrase(text, terms):
                if key == "services":
                    return "Our listed services are: " + ", ".join(self.clinic.get("services", [])) + "."
                return f"Our {key} are: {self.clinic.get(key, 'Please contact clinic staff for details')}."

        if has_phrase(text, ("diagnosis", "diagnose", "medicine", "medication", "prescription")):
            return (
                "I can share clinic information, but I cannot diagnose conditions "
                "or recommend medicines. Please speak with a qualified healthcare professional."
            )

        if has_phrase(text, ("i am ill", "i'm ill", "i feel ill", "i am sick", "i'm sick",
                             "feeling unwell", "not feeling well", "i feel unwell",
                             "very ill", "very sick")):
            return (
                "I'm sorry you're feeling unwell. I cannot assess symptoms. If you think "
                "this may be an emergency, seek urgent medical care. Otherwise, type "
                "'appointment' if you would like to submit a request."
            )

        return (
            "I'm not sure about that. I can help with clinic hours, address, contact "
            "details, fees, services and appointment requests. For other questions, "
            "please contact clinic staff."
        )

def main():
    clinic = load_clinic()
    assistant = ClinicAssistant(clinic)
    print("=" * 48)
    print(f"Welcome to {clinic['name']} — Customer Support")
    print("=" * 48)
    print("Demo prototype. Use fictional details only.")
    print("Type 'help' for options or 'exit' to quit.")
    while True:
        try:
            message = input("\nYou: ")
        except (EOFError, KeyboardInterrupt):
            print("\\nGoodbye!")
            break
        print(f"\n{clinic['name']} Assistant: {assistant.reply(message)}")
        if normalize(message) in {"exit", "quit", "bye"}:
            break

if __name__ == "__main__":
    main()
