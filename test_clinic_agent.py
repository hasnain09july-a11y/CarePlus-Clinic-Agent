import tempfile
import unittest
from pathlib import Path
from clinic_agent import ClinicAssistant, DEFAULT_CLINIC

class ClinicAssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "requests.json"
        self.bot = ClinicAssistant(DEFAULT_CLINIC.copy(), self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_greeting(self):
        self.assertIn("Welcome", self.bot.reply("hello"))

    def test_hours(self):
        self.assertIn("Monday to Saturday", self.bot.reply("What are your hours?"))

    def test_appointment_needs_confirmation(self):
        self.assertIn("yes or no", self.bot.reply("I need an appointment"))
        self.assertEqual(self.bot.state, "confirm")

    def test_no_does_not_save(self):
        self.bot.reply("appointment")
        self.bot.reply("no")
        self.assertFalse(self.path.exists())

    def test_full_request_flow(self):
        self.bot.reply("appointment")
        self.bot.reply("yes")
        self.bot.reply("Demo Patient")
        self.bot.reply("demo@example.com")
        self.bot.reply("25 November 2026")
        result = self.bot.reply("10:30 AM")
        self.assertIn("NOT a confirmed appointment", result)
        self.assertTrue(self.path.exists())

    def test_cancel(self):
        self.bot.reply("appointment")
        self.bot.reply("yes")
        self.bot.reply("cancel")
        self.assertEqual(self.bot.state, "idle")
        self.assertEqual(self.bot.pending, {})

    def test_emergency_warning(self):
        result = self.bot.reply("I have chest pain")
        self.assertIn("emergency", result.lower())
        self.assertEqual(self.bot.state, "idle")

    def test_empty_message(self):
        self.assertIn("Please type", self.bot.reply(" "))

if __name__ == "__main__":
    unittest.main()
