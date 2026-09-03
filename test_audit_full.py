import unittest
from audit_full import norm_url, event_date, flat, candidate_passages, city_patterns
from audit_finalize import band, exact_in_body, effective_event, mark_event_date


class AuditRules(unittest.TestCase):
    def test_city_aliases(self):
        self.assertTrue(city_patterns()["Kyiv"].search("у Києві"))
        self.assertTrue(city_patterns()["Lviv"].search("Львові"))

    def test_amp_and_tracking(self):
        self.assertEqual(norm_url("https://www.suspilne.media/amp/dnipro/123-title/?utm_source=x"),
                         norm_url("https://suspilne.media/dnipro/123-title/"))
        self.assertEqual(norm_url("https://news.example/a.html/amp"), norm_url("https://news.example/a.html"))

    def test_meaningful_query_preserved(self):
        self.assertNotEqual(norm_url("https://example.org/?id=1"), norm_url("https://example.org/?id=2"))
        self.assertNotEqual(norm_url("https://example.org/a?ref=article1"), norm_url("https://example.org/a"))

    def test_retrospective_event_date(self):
        self.assertEqual(event_date({"published": "21.08 (подія 19.08)"}), "2026-08-19")
        self.assertEqual(event_date({"published": "16.07.2025"}), "2025-07-16")
        self.assertIsNone(event_date({"published": "31.02"}))
        self.assertIsNone(event_date({"published": "05.08 (подія не датована)"}))

    def test_quote_normalization_is_not_rewriting(self):
        self.assertEqual(flat("Близько\u00a0100\nлюдей"), "Близько 100 людей")
        self.assertNotEqual(flat("близько сотні людей"), flat("близько 100 людей"))

    def test_vague_count_is_a_candidate_not_a_value(self):
        passages = candidate_passages("Дніпро\nКілька сотень людей вийшли на акцію.")
        self.assertEqual(len(passages), 1)
        self.assertNotIn("value", passages[0])

    def test_unrelated_number_not_promoted(self):
        self.assertEqual(candidate_passages("82-річний учасник розповів свою історію."), [])
        self.assertEqual(candidate_passages("36-й день протестів."), [])

    def test_context_preserves_multicity_and_update(self):
        text = "Дніпро\nБлизько ста людей зібралися.\nПісля ходи долучилися близько 500 людей.\nКиїв\nБлизько 6000 людей."
        passages = candidate_passages(text)
        self.assertEqual(len(passages), 3)
        self.assertIn("Дніпро", passages[0]["context"])
        self.assertIn("Київ", passages[2]["context"])

    def test_small_spelled_counts(self):
        self.assertEqual(len(candidate_passages("До заходу долучилися восьмеро людей.")), 1)
        self.assertEqual(len(candidate_passages("На початку на акцію вийшли двоє людей.")), 1)
        self.assertEqual(candidate_passages("Учасники тривають у своїх вимогах."), [])

    def test_unavailable_body_cannot_validate_quote(self):
        self.assertFalse(exact_in_body("Близько 100 людей", ""))
        self.assertTrue(exact_in_body("невідомо", ""))

    def test_rewritten_quote_does_not_match(self):
        self.assertFalse(exact_in_body("близько 100 людей", "зібралося близько сотні людей"))
        self.assertTrue(exact_in_body("«близько сотні людей»", "зібралося близько\nсотні людей"))

    def test_meaningful_parameters_and_cross_run_identity(self):
        self.assertNotEqual(norm_url("https://example.org/news?page=1"), norm_url("https://example.org/news?page=2"))
        self.assertEqual(norm_url("https://example.org/news?id=1&utm_source=x"), norm_url("https://example.org/news?id=1"))
        self.assertNotEqual(("Kyiv", "url", "6 Aug"), ("Kyiv", "url", "3 Sep"))

    def test_date_uncertainty_does_not_use_publication_as_event(self):
        self.assertEqual(effective_event({"city":"Kyiv","published":"28.07"},{},{"outcome":"unresolved_date"}), (None,True))
        self.assertEqual(mark_event_date("01.08, 12:30", "2026-07-31"), "01.08, 12:30 (подія 31.07)")

    def test_multicity_override(self):
        review = {"event_dates":{"Kyiv":"2026-07-31","Lviv":"2026-08-01"}}
        self.assertEqual(effective_event({"city":"Lviv","published":"02.08"},{},review), ("2026-08-01",False))

    def test_categories_do_not_turn_missing_into_zero(self):
        self.assertEqual(band(None), "unknown")
        self.assertEqual(band(99), "<100")
        self.assertEqual(band(100), "100–999")
        self.assertEqual(band(1000), "1000–4999")

    def test_casualties_and_background_remain_candidates_only(self):
        passages = candidate_passages("У 2024 році загинули 100 людей. Сьогодні учасники вийшли на протест.")
        self.assertTrue(passages)
        self.assertNotIn("value", passages[0])


if __name__ == "__main__":
    unittest.main()
