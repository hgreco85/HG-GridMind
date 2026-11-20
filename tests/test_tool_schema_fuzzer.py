import unittest
from tool_schema_fuzzer import ToolSchemaFuzzer, ToolValidator, SchemaValidationError


class TestToolSchemaFuzzer(unittest.TestCase):

    def setUp(self):
        self.fuzzer = ToolSchemaFuzzer(seed=1337)
        self.sample_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["tool_name", "query", "limit"],
            "properties": {
                "tool_name": {
                    "type": "string",
                    "enum": ["search_engine", "vector_db"]
                },
                "query": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100
                },
                "tags": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 5,
                    "items": {"type": "string"}
                },
                "is_strict": {
                    "type": "boolean"
                }
            }
        }

    def test_valid_call_generation_and_validation(self):
        valid_call = self.fuzzer.generate_valid_call(self.sample_schema)
        # Verify that generated valid call strictly passes validation
        try:
            ToolValidator.validate(self.sample_schema, valid_call)
        except SchemaValidationError as e:
            self.fail(f"Generated call unexpectedly failed validation: {e}")

        self.assertIn(valid_call["tool_name"], ["search_engine", "vector_db"])
        self.assertTrue(3 <= len(valid_call["query"]) <= 50)
        self.assertTrue(1 <= valid_call["limit"] <= 100)

    def test_negative_boundary_cases_trigger_validation_errors(self):
        boundary_cases = self.fuzzer.generate_negative_boundary_cases(self.sample_schema)
        self.assertGreaterEqual(len(boundary_cases), 8)

        # Every negative boundary test case must raise SchemaValidationError
        for case_name, malformed_payload in boundary_cases:
            with self.subTest(case=case_name):
                with self.assertRaises(SchemaValidationError, msg=f"Failed to reject: {case_name}"):
                    ToolValidator.validate(self.sample_schema, malformed_payload)

    def test_fuzzer_determinism_and_reproducibility(self):
        fuzzer_1 = ToolSchemaFuzzer(seed=42)
        cases_1 = fuzzer_1.fuzz_random_mutations(self.sample_schema, count=5)

        fuzzer_2 = ToolSchemaFuzzer(seed=42)
        cases_2 = fuzzer_2.fuzz_random_mutations(self.sample_schema, count=5)

        # Exact matching across identical seeds
        self.assertEqual(cases_1, cases_2)

        # Reset should produce the exact same sequence
        fuzzer_1.reset(seed=42)
        cases_1_reset = fuzzer_1.fuzz_random_mutations(self.sample_schema, count=5)
        self.assertEqual(cases_1, cases_1_reset)

    def test_unexpected_parameters_and_type_boundary(self):
        # Additional properties rejection
        strict_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["cmd"],
            "properties": {
                "cmd": {"type": "string"}
            }
        }
        with self.assertRaises(SchemaValidationError):
            ToolValidator.validate(strict_schema, {"cmd": "run", "extra_arg": 42})

        # Boolean supplied for numeric property must be rejected
        numeric_schema = {
            "type": "object",
            "required": ["count"],
            "properties": {
                "count": {"type": "integer", "minimum": 0}
            }
        }
        with self.assertRaises(SchemaValidationError):
            ToolValidator.validate(numeric_schema, {"count": True})


if __name__ == "__main__":
    unittest.main()
