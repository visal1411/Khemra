from django.test import SimpleTestCase

from apps.rag.services.ScoreCombiner import ScoreCombiner


class ScoreCombinerTest(SimpleTestCase):
    def test_weighted_average(self):
        c = ScoreCombiner({"question": 0.5, "summary": 0.5})
        s = c.combine("S1", {"question": 1.0, "summary": 0.5, "topic": 0.9})
        self.assertAlmostEqual(s.score, 0.75)           # topic has weight 0 -> ignored
        self.assertEqual(s.confidence, 75.0)
        self.assertEqual(s.best_match, "question")
        self.assertEqual(s.confidence_by_type["question"], 100.0)
        self.assertEqual(s.confidence_by_type["topic"], 90.0)   # still reported

    def test_missing_type_renormalises(self):
        s = ScoreCombiner().combine("S1", {"topic": 0.8})
        self.assertAlmostEqual(s.score, 0.8)

    def test_negative_similarity_counts_as_zero(self):
        s = ScoreCombiner({"topic": 1}).combine("S1", {"topic": -0.4})
        self.assertEqual(s.score, 0.0)
        self.assertEqual(s.confidence_by_type["topic"], 0.0)

    def test_bad_weights(self):
        with self.assertRaises(ValueError):
            ScoreCombiner({"nope": 1})
        with self.assertRaises(ValueError):
            ScoreCombiner({"topic": 0})
