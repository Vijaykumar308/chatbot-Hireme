import unittest

from src.services.llm import build_personal_details_response, format_llm_error_message


class ProfileGuardrailTests(unittest.TestCase):
    def test_salary_queries_are_redirected_safely(self):
        response = build_personal_details_response(
            "What is my expected CTC?",
            "My expected CTC is ₹7-10 LPA. Contact: +91 98765 43210 | me@example.com",
        )

        self.assertIsNotNone(response)
        text = response.lower()
        self.assertIn("ctc", text)
        self.assertIn("contact", text)
        self.assertIn("private", text)
        self.assertNotIn("₹7", response)
        self.assertNotIn("98765", response)

    def test_contact_queries_can_return_contact_details(self):
        response = build_personal_details_response(
            "What is my contact number?",
            "Phone: +91 98765 43210 Email: me@example.com",
        )

        self.assertIsNotNone(response)
        self.assertIn("+91 98765 43210", response)

    def test_rate_limit_errors_are_formatted_gracefully(self):
        message = format_llm_error_message(
            "Error code: 429 - {'error': {'message': 'Rate limit reached for model `llama-3.3-70b-versatile`...'}}"
        )

        self.assertIn("temporarily unavailable", message.lower())
        self.assertIn("try again", message.lower())
        self.assertNotIn("rate limit reached", message.lower())
        self.assertNotIn("llama-3.3-70b-versatile", message)

    def test_resume_style_name_and_contact_are_extracted(self):
        context = """VIJAY KUMAR
+91 8054975142⋄Sec-32 Gurugram
jwvijaykumar@gmail.com⋄linkedin.com/in/vijay-kumar-679ab2221/⋄https://github.com/Vijaykumar308/
OBJECTIVE
Software Engineer"""

        response = build_personal_details_response("what is my name and contact number?", context)

        self.assertIsNotNone(response)
        self.assertIn("VIJAY KUMAR", response)
        self.assertIn("8054975142", response)
        self.assertIn("jwvijaykumar@gmail.com", response)


if __name__ == "__main__":
    unittest.main()
