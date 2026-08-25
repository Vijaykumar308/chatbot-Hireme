import unittest

from src.services.llm import build_personal_details_response, format_llm_error_message
from src.routes.chat import _profile_query_terms


class ProfileGuardrailTests(unittest.TestCase):
    def test_salary_queries_do_not_reveal_compensation(self):
        response = build_personal_details_response(
            "What is my expected CTC?",
            "My expected CTC is ₹7-10 LPA. Contact: +91 98765 43210 | me@example.com",
        )

        self.assertIsNotNone(response)
        self.assertIn("do not share compensation", response.lower())
        self.assertNotIn("7-10", response)

    def test_contact_queries_are_delegated_to_the_llm(self):
        response = build_personal_details_response(
            "What is my contact number?",
            "Phone: +91 98765 43210 Email: me@example.com",
        )

        self.assertIsNone(response)

    def test_rate_limit_errors_are_formatted_gracefully(self):
        message = format_llm_error_message(
            "Error code: 429 - {'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b`...'}}"
        )

        self.assertIn("temporarily unavailable", message.lower())
        self.assertIn("try again", message.lower())
        self.assertNotIn("rate limit reached", message.lower())
        self.assertNotIn("openai/gpt-oss-120b", message)

    def test_name_questions_use_profile_name_fallback(self):
        response = build_personal_details_response("what is your name?", "Software Developer | Full Stack Developer")

        self.assertIsNotNone(response)
        self.assertIn("Vijay", response)
        self.assertIn("Kumar", response)

    def test_name_questions_never_use_a_heading_as_name(self):
        response = build_personal_details_response("what is your name?", "Education\nHireMe\nSoftware Developer")

        self.assertEqual(response, "My name is Vijay Kumar.")

    def test_resume_style_name_is_extracted(self):
        context = """VIJAY KUMAR
+91 8054975142⋄Sec-32 Gurugram
jwvijaykumar@gmail.com⋄linkedin.com/in/vijay-kumar-679ab2221/⋄https://github.com/Vijaykumar308/
OBJECTIVE
Software Engineer"""

        response = build_personal_details_response("what is my name and contact number?", context)

        self.assertIsNotNone(response)
        self.assertIn("VIJAY KUMAR", response)

    def test_experience_and_company_queries_use_resume_terms(self):
        terms = _profile_query_terms("How many years of experience do you have and what is your last company?")

        self.assertIn("4+ years", terms)
        self.assertIn("Kochar Tech", terms)


if __name__ == "__main__":
    unittest.main()
