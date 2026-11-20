import copy
import random
from typing import Any, Dict, List, Optional, Tuple, Union


class SchemaValidationError(Exception):
    """Raised when input parameters fail validation against a tool schema."""
    pass


class ToolValidator:
    """Validates tool calls against a simplified JSON-schema-like dictionary."""

    @staticmethod
    def validate(schema: Dict[str, Any], call_args: Dict[str, Any]) -> None:
        if not isinstance(call_args, dict):
            raise SchemaValidationError(f"Arguments must be a dict, got {type(call_args).__name__}")

        schema_type = schema.get("type", "object")
        if schema_type != "object":
            raise SchemaValidationError(f"Root schema type must be 'object', got '{schema_type}'")

        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional_props = schema.get("additionalProperties", True)

        # Check required fields
        for req in required:
            if req not in call_args:
                raise SchemaValidationError(f"Missing required parameter: '{req}'")

        # Check unknown parameters if additionalProperties is False
        if not additional_props:
            for param in call_args:
                if param not in properties:
                    raise SchemaValidationError(f"Unexpected parameter: '{param}'")

        # Validate parameter types and constraints
        for param, value in call_args.items():
            if param not in properties:
                continue
            prop_schema = properties[param]
            ToolValidator._validate_property(param, prop_schema, value)

    @staticmethod
    def _validate_property(name: str, prop_schema: Dict[str, Any], value: Any) -> None:
        expected_type = prop_schema.get("type")
        nullable = prop_schema.get("nullable", False)

        if value is None:
            if not nullable:
                raise SchemaValidationError(f"Parameter '{name}' cannot be null")
            return

        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        if expected_type in type_map:
            expected_cls = type_map[expected_type]
            # In Python, bool is a subclass of int, so handle strict bool vs number check
            if expected_type in ("integer", "number") and isinstance(value, bool):
                raise SchemaValidationError(f"Parameter '{name}' expected type '{expected_type}', got boolean")
            if expected_type == "string" and not isinstance(value, str):
                raise SchemaValidationError(f"Parameter '{name}' expected type 'string', got {type(value).__name__}")
            if not isinstance(value, expected_cls):
                raise SchemaValidationError(f"Parameter '{name}' expected type '{expected_type}', got {type(value).__name__}")

        # String constraints
        if expected_type == "string" and isinstance(value, str):
            if "minLength" in prop_schema and len(value) < prop_schema["minLength"]:
                raise SchemaValidationError(f"Parameter '{name}' string length {len(value)} < minLength {prop_schema['minLength']}")
            if "maxLength" in prop_schema and len(value) > prop_schema["maxLength"]:
                raise SchemaValidationError(f"Parameter '{name}' string length {len(value)} > maxLength {prop_schema['maxLength']}")

        # Numeric constraints
        if expected_type in ("integer", "number") and isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in prop_schema and value < prop_schema["minimum"]:
                raise SchemaValidationError(f"Parameter '{name}' value {value} < minimum {prop_schema['minimum']}")
            if "maximum" in prop_schema and value > prop_schema["maximum"]:
                raise SchemaValidationError(f"Parameter '{name}' value {value} > maximum {prop_schema['maximum']}")

        # Enum constraints
        if "enum" in prop_schema:
            if value not in prop_schema["enum"]:
                raise SchemaValidationError(f"Parameter '{name}' value {value!r} not in enum {prop_schema['enum']}")

        # Array constraints
        if expected_type == "array" and isinstance(value, list):
            if "minItems" in prop_schema and len(value) < prop_schema["minItems"]:
                raise SchemaValidationError(f"Parameter '{name}' items count {len(value)} < minItems {prop_schema['minItems']}")
            if "maxItems" in prop_schema and len(value) > prop_schema["maxItems"]:
                raise SchemaValidationError(f"Parameter '{name}' items count {len(value)} > maxItems {prop_schema['maxItems']}")
            item_schema = prop_schema.get("items")
            if item_schema:
                for idx, item in enumerate(value):
                    ToolValidator._validate_property(f"{name}[{idx}]", item_schema, item)


class ToolSchemaFuzzer:
    """Deterministic tool calling schema fuzzer for negative boundary and invalid input testing."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def reset(self, seed: Optional[int] = None) -> None:
        """Reset internal RNG seed for reproducible test sequences."""
        if seed is not None:
            self.seed = seed
        self.rng = random.Random(self.seed)

    def generate_valid_call(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a minimal valid call satisfying the given schema."""
        properties = schema.get("properties", {})
        required = schema.get("required", list(properties.keys()))
        valid_call = {}

        for prop_name in required:
            if prop_name in properties:
                valid_call[prop_name] = self._generate_valid_value(properties[prop_name])
        return valid_call

    def _generate_valid_value(self, prop_schema: Dict[str, Any]) -> Any:
        prop_type = prop_schema.get("type", "string")
        if "enum" in prop_schema and prop_schema["enum"]:
            return prop_schema["enum"][0]

        if prop_type == "string":
            min_len = prop_schema.get("minLength", 1)
            return "a" * max(min_len, 1)
        elif prop_type == "integer":
            min_val = prop_schema.get("minimum", 0)
            max_val = prop_schema.get("maximum", min_val + 10)
            return min_val
        elif prop_type == "number":
            min_val = prop_schema.get("minimum", 0.0)
            return float(min_val)
        elif prop_type == "boolean":
            return True
        elif prop_type == "array":
            min_items = prop_schema.get("minItems", 0)
            item_schema = prop_schema.get("items", {"type": "string"})
            return [self._generate_valid_value(item_schema) for _ in range(min_items)]
        elif prop_type == "object":
            return {}
        return "valid_default"

    def generate_negative_boundary_cases(self, schema: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """Produces a deterministic list of (failure_reason, malformed_payload) test cases."""
        cases: List[Tuple[str, Dict[str, Any]]] = []
        base_valid = self.generate_valid_call(schema)
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional_props = schema.get("additionalProperties", True)

        # 1. Missing required parameters
        for req in sorted(required):
            if req in base_valid:
                mutated = copy.deepcopy(base_valid)
                del mutated[req]
                cases.append((f"missing_required_{req}", mutated))

        # 2. Unexpected parameters if additionalProperties is False
        if not additional_props:
            mutated = copy.deepcopy(base_valid)
            mutated["__unexpected_param__"] = "illegal_value"
            cases.append(("unexpected_parameter", mutated))

        # 3. Property boundary and type mutations
        for prop_name in sorted(properties.keys()):
            prop_schema = properties[prop_name]
            prop_type = prop_schema.get("type")
            nullable = prop_schema.get("nullable", False)

            # Null injection
            if not nullable:
                mutated = copy.deepcopy(base_valid)
                mutated[prop_name] = None
                cases.append((f"null_type_{prop_name}", mutated))

            # Wrong primitive type injection
            wrong_types = {
                "string": 12345,
                "integer": "not_an_int",
                "number": "not_a_number",
                "boolean": "false",
                "array": {"not": "an_array"},
                "object": ["not_an_object"],
            }
            if prop_type in wrong_types:
                mutated = copy.deepcopy(base_valid)
                mutated[prop_name] = wrong_types[prop_type]
                cases.append((f"invalid_type_{prop_name}", mutated))

            # Boolean as integer negative boundary check
            if prop_type in ("integer", "number"):
                mutated = copy.deepcopy(base_valid)
                mutated[prop_name] = True
                cases.append((f"bool_as_numeric_{prop_name}", mutated))

            # String bounds
            if prop_type == "string":
                if "minLength" in prop_schema and prop_schema["minLength"] > 0:
                    mutated = copy.deepcopy(base_valid)
                    mutated[prop_name] = "a" * (prop_schema["minLength"] - 1)
                    cases.append((f"string_under_min_length_{prop_name}", mutated))
                if "maxLength" in prop_schema:
                    mutated = copy.deepcopy(base_valid)
                    mutated[prop_name] = "a" * (prop_schema["maxLength"] + 1)
                    cases.append((f"string_over_max_length_{prop_name}", mutated))

            # Numeric bounds
            if prop_type in ("integer", "number"):
                if "minimum" in prop_schema:
                    mutated = copy.deepcopy(base_valid)
                    mutated[prop_name] = prop_schema["minimum"] - 1
                    cases.append((f"numeric_below_min_{prop_name}", mutated))
                if "maximum" in prop_schema:
                    mutated = copy.deepcopy(base_valid)
                    mutated[prop_name] = prop_schema["maximum"] + 1
                    cases.append((f"numeric_above_max_{prop_name}", mutated))

            # Enum violations
            if "enum" in prop_schema:
                mutated = copy.deepcopy(base_valid)
                mutated[prop_name] = "__not_in_enum_sentinel__"
                cases.append((f"invalid_enum_{prop_name}", mutated))

            # Array bounds
            if prop_type == "array":
                if "minItems" in prop_schema and prop_schema["minItems"] > 0:
                    mutated = copy.deepcopy(base_valid)
                    mutated[prop_name] = []
                    cases.append((f"array_under_min_items_{prop_name}", mutated))
                if "maxItems" in prop_schema:
                    mutated = copy.deepcopy(base_valid)
                    item_val = self._generate_valid_value(prop_schema.get("items", {"type": "string"}))
                    mutated[prop_name] = [item_val] * (prop_schema["maxItems"] + 1)
                    cases.append((f"array_over_max_items_{prop_name}", mutated))

        return cases

    def fuzz_random_mutations(
        self, schema: Dict[str, Any], count: int = 10
    ) -> List[Dict[str, Any]]:
        """Generates deterministically fuzzed malformed payloads using pseudo-random mutations."""
        self.reset()
        fuzzed_cases = []
        base = self.generate_valid_call(schema)
        properties = schema.get("properties", {})
        prop_keys = sorted(properties.keys())

        for _ in range(count):
            mutated = copy.deepcopy(base)
            mutation_type = self.rng.choice(["corrupt_value", "drop_field", "insert_garbage"])

            if mutation_type == "drop_field" and mutated:
                target_field = self.rng.choice(list(mutated.keys()))
                del mutated[target_field]
            elif mutation_type == "insert_garbage":
                random_key = f"fuzz_key_{self.rng.randint(1000, 9999)}"
                mutated[random_key] = self.rng.choice([None, -9999, "malformed", [1, 2, 3]])
            else:  # corrupt_value
                if prop_keys:
                    field = self.rng.choice(prop_keys)
                    mutated[field] = self.rng.choice([
                        float("inf"),
                        float("-inf"),
                        -9999999999999999,
                        "\x00\xFFspecial_chars",
                        None,
                        [],
                        {},
                    ])
            fuzzed_cases.append(mutated)
        return fuzzed_cases
