# CarePlus Clinic Customer Support Prototype

A Python command-line prototype that answers basic clinic FAQs and records appointment **requests** for staff review.

## Features
- Configurable FAQs from `clinic_config.json`
- Stateful appointment conversation (confirmation, name, contact, date, time)
- Basic input validation and cancellation
- JSON storage with a unique request reference
- Error handling and automated unit tests

## Requirements
Python 3.10 or newer. No third-party packages required.

## Run
Open a terminal in this folder:
```bash
python clinic_agent.py
```

## Run tests
```bash
python -m unittest -v
```

## Demo data
The address and phone are fictional placeholders. Edit `clinic_config.json` to change them. Use fictional patient details while testing.

## Limitations and safety
- This is a rule-based prototype, not an LLM-powered AI agent.
- It does not connect to a calendar, check availability, or confirm appointments.
- It only saves a request marked `Pending clinic confirmation`.
- Emergency phrase matching is limited and is not medical triage. It cannot assess urgency.
- Do not use real patient information. JSON stores contact details in plain text.
- Real deployment would require clinic authorization, privacy/legal review, secure storage, access controls, staff workflows and professional safety review.

## Portfolio description
**CarePlus Clinic Customer Support Prototype** — Built a Python command-line assistant that answers configurable clinic FAQs and guides users through a stateful appointment-request flow. Implemented JSON persistence, input validation, cancellation, error handling and automated unit tests. The prototype does not diagnose, provide treatment advice, check live availability or confirm appointments.
