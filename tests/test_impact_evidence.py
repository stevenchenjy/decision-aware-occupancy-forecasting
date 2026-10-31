import unittest
from scripts.capture_impact import participation


class ParticipationEvidenceTests(unittest.TestCase):
    def test_owner_bots_and_pull_requests_are_not_outside_interest(self):
        stars = {"available": True, "data": [{"login": "Owner", "type": "User"}, {"login": "ci[bot]", "type": "Bot"}, {"login": "reader", "type": "User"}]}
        def issue(number, login, **extra):
            return {"number": number, "title": "Reproduction: attempt", "html_url": "https://example.test/" + str(number), "state": "open", "user": {"login": login, "type": "User"}, **extra}
        issues = {"available": True, "data": [issue(1, "owner"), issue(2, "reader", pull_request={"url": "https://example.test/pr/2"}), issue(3, "reader"), issue(4, "ci[bot]")]}
        result = participation("owner", stars, issues)
        self.assertTrue(result["owner_has_starred"])
        self.assertEqual(result["non_owner_non_bot_star_accounts"], ["reader"])
        self.assertEqual(result["reproduction_report_candidates"], [3])
        self.assertEqual(len(result["non_owner_non_bot_issues"]), 1)
        self.assertNotIn("successful_reproductions", result)

    def test_unavailable_activity_stays_unknown_instead_of_becoming_zero(self):
        unavailable = {"available": False, "error": "Access unavailable"}
        result = participation("owner", unavailable, unavailable)
        self.assertFalse(result["stars_available"])
        self.assertFalse(result["issues_available"])
        self.assertNotIn("non_owner_non_bot_star_accounts", result)
        self.assertNotIn("reproduction_report_candidates", result)


if __name__ == "__main__":
    unittest.main()
