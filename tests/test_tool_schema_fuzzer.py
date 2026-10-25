import unittest
from tool_schema_fuzzer import ToolSchemaFuzzer, SchemaValidationError, validate_payload


class TestToolSchemaFuzzer(unittest.TestCase):
    def setUp(self):
        self.fuzzer = ToolSchemaFuzzer(seed=1337)
        self.sample_tool_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["action", "count"],
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "delete"],
                    "minLength": 3,
                    "maxLength": 10,
                },
                "count": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
            },
        }

    def test_deterministic_generation(self):
        """Verify that re-seeding produces identical payloads deterministically."""
        self.fuzzer.reseed(42)
        payload_1 = self.fuzzer.generate_valid_payload(self.sample_tool_schema)
        mutations_1 = self.fuzzer.generate_boundary_mutations(self.sample_tool_schema)

        self.fuzzer.reseed(42)
        payload_2 = self.fuzzer.generate_valid_payload(self.sample_tool_schema)
        mutations_2 = self.fuzzer.generate_boundary_mutations(self.sample_tool_schema)

        self.assertEqual(payload_1, payload_2)
        self.assertEqual(mutations_1, mutations_2)
        # Valid payload must pass validation
        validate_payload(self.sample_tool_schema, payload_1)

    def test_negative_boundary_mutations_rejection(self):
        """Verify that all generated negative boundary mutations are rejected by validator."""
        results = self.fuzzer.fuzz_and_validate(self.sample_tool_schema)
        self.assertGreater(results["total_mutations"], 0)
        self.assertEqual(results["total_mutations"], results["passed_negatives"])
        for detail in results["details"]:
            self.assertTrue(detail["rejected"], f"Failed to reject mutation: {detail['category']}")

    def test_missing_required_property_boundary(self):
        """Verify that omission of required fields triggers SchemaValidationError."""
        payload = self.fuzzer.generate_valid_payload(self.sample_tool_schema)
        del payload["action"]
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_payload(self.sample_tool_schema, payload)
        self.assertIn("Missing required property: 'action'", str(ctx.exception))

    def test_numeric_boundary_limits(self):
        """Verify minimum and maximum boundary enforcement on numeric parameters."""
        payload = self.fuzzer.generate_valid_payload(self.sample_tool_schema)
        # Underflow
        payload["count"] = 0
        with self.assertRaises(SchemaValidationError):
            validate_payload(self.sample_tool_schema, payload)

        # Exact minimum is valid
        payload["count"] = 1
        validate_payload(self.sample_tool_schema, payload)

        # Exact maximum is valid
        payload["count"] = 100
        validate_payload(self.sample_tool_schema, payload)

        # Overflow
        payload["count"] = 101
        with self.assertRaises(SchemaValidationError):
            validate_payload(self.sample_tool_schema, payload)

    def test_unexpected_property_rejection(self):
        """Verify additionalProperties=False prevents arbitrary injected arguments."""
        payload = self.fuzzer.generate_valid_payload(self.sample_tool_schema)
        payload["unauthorized_field"] = "malicious_payload"
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_payload(self.sample_tool_schema, payload)
        self.assertIn("Additional property not allowed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
