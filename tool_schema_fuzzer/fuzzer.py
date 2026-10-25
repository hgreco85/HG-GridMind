import copy
import random
from typing import Any, Dict, List, Optional, Tuple


class SchemaValidationError(Exception):
    """Raised when input payload fails JSON schema validation."""
    pass


def validate_payload(schema: Dict[str, Any], payload: Any) -> None:
    """Validate payload strictly against a simplified JSON Schema specification."""
    if not isinstance(schema, dict):
        return

    schema_type = schema.get("type")
    if schema_type is not None:
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        expected_type = type_map.get(schema_type)
        if expected_type is not None:
            # Python bool is a subclass of int, disallow bool for integer/number
            if schema_type in ("integer", "number") and isinstance(payload, bool):
                raise SchemaValidationError(f"Expected {schema_type}, got bool for {payload}")
            if not isinstance(payload, expected_type):
                raise SchemaValidationError(
                    f"Expected type {schema_type}, got {type(payload).__name__} for {payload}"
                )

    if isinstance(payload, str):
        min_len = schema.get("minLength")
        max_len = schema.get("maxLength")
        if min_len is not None and len(payload) < min_len:
            raise SchemaValidationError(f"String length {len(payload)} < minLength {min_len}")
        if max_len is not None and len(payload) > max_len:
            raise SchemaValidationError(f"String length {len(payload)} > maxLength {max_len}")

    elif isinstance(payload, (int, float)) and not isinstance(payload, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and payload < minimum:
            raise SchemaValidationError(f"Numeric value {payload} < minimum {minimum}")
        if maximum is not None and payload > maximum:
            raise SchemaValidationError(f"Numeric value {payload} > maximum {maximum}")

    elif isinstance(payload, list):
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if min_items is not None and len(payload) < min_items:
            raise SchemaValidationError(f"Array length {len(payload)} < minItems {min_items}")
        if max_items is not None and len(payload) > max_items:
            raise SchemaValidationError(f"Array length {len(payload)} > maxItems {max_items}")
        items_schema = schema.get("items")
        if items_schema:
            for idx, elem in enumerate(payload):
                try:
                    validate_payload(items_schema, elem)
                except SchemaValidationError as e:
                    raise SchemaValidationError(f"Array element {idx} invalid: {e}") from e

    elif isinstance(payload, dict):
        required = schema.get("required", [])
        for req_prop in required:
            if req_prop not in payload:
                raise SchemaValidationError(f"Missing required property: '{req_prop}'")
        properties = schema.get("properties", {})
        for key, val in payload.items():
            if key in properties:
                try:
                    validate_payload(properties[key], val)
                except SchemaValidationError as e:
                    raise SchemaValidationError(f"Property '{key}' invalid: {e}") from e
            elif schema.get("additionalProperties") is False:
                raise SchemaValidationError(f"Additional property not allowed: '{key}'")

    enum_values = schema.get("enum")
    if enum_values is not None and payload not in enum_values:
        raise SchemaValidationError(f"Value {payload!r} not in enum {enum_values}")


class ToolSchemaFuzzer:
    """Deterministic JSON Schema fuzzer for testing tool-calling interfaces."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def reseed(self, seed: Optional[int] = None) -> None:
        """Reset internal RNG seed to guarantee determinism."""
        if seed is not None:
            self.seed = seed
        self.rng = random.Random(self.seed)

    def generate_valid_payload(self, schema: Dict[str, Any]) -> Any:
        """Generate a canonical conforming payload matching the schema."""
        schema_type = schema.get("type", "object")
        if "enum" in schema:
            enum_candidates = schema["enum"]
            return enum_candidates[0] if enum_candidates else None

        if schema_type == "string":
            min_len = schema.get("minLength", 1)
            return "a" * max(min_len, 1)

        if schema_type == "integer":
            minimum = schema.get("minimum", 0)
            return minimum

        if schema_type == "number":
            minimum = schema.get("minimum", 0.0)
            return float(minimum)

        if schema_type == "boolean":
            return True

        if schema_type == "array":
            min_items = schema.get("minItems", 0)
            items_schema = schema.get("items", {"type": "string"})
            count = max(min_items, 1) if min_items > 0 else 1
            return [self.generate_valid_payload(items_schema) for _ in range(count)]

        if schema_type == "object":
            properties = schema.get("properties", {})
            required = schema.get("required", list(properties.keys()))
            result = {}
            for prop in required:
                prop_schema = properties.get(prop, {})
                result[prop] = self.generate_valid_payload(prop_schema)
            return result

        return {}

    def generate_boundary_mutations(self, schema: Dict[str, Any]) -> List[Tuple[str, Any]]:
        """Generate negative boundary mutations that violate schema constraints.

        Returns a list of tuples (violation_category, mutated_payload).
        """
        mutations: List[Tuple[str, Any]] = []
        base_payload = self.generate_valid_payload(schema)

        if schema.get("type") == "object":
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            # 1. Missing required field mutations
            for req_key in required:
                payload_missing = copy.deepcopy(base_payload)
                if req_key in payload_missing:
                    del payload_missing[req_key]
                    mutations.append((f"missing_required_{req_key}", payload_missing))

            # 2. Unexpected property injection mutation
            if schema.get("additionalProperties") is False:
                payload_unexpected = copy.deepcopy(base_payload)
                payload_unexpected["__unexpected_fuzzer_prop__"] = "illegal_value"
                mutations.append(("unexpected_property", payload_unexpected))

            # 3. Type violation and boundary mutations for each property
            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get("type")
                # Type mismatch
                if prop_type == "string":
                    payload_bad_type = copy.deepcopy(base_payload)
                    payload_bad_type[prop_name] = 123456
                    mutations.append((f"bad_type_{prop_name}", payload_bad_type))

                    # minLength boundary violation
                    min_len = prop_schema.get("minLength")
                    if min_len is not None and min_len > 0:
                        payload_short = copy.deepcopy(base_payload)
                        payload_short[prop_name] = "a" * (min_len - 1)
                        mutations.append((f"underflow_length_{prop_name}", payload_short))

                    # maxLength boundary violation
                    max_len = prop_schema.get("maxLength")
                    if max_len is not None:
                        payload_long = copy.deepcopy(base_payload)
                        payload_long[prop_name] = "a" * (max_len + 1)
                        mutations.append((f"overflow_length_{prop_name}", payload_long))

                elif prop_type in ("integer", "number"):
                    payload_bad_type = copy.deepcopy(base_payload)
                    payload_bad_type[prop_name] = "not_a_number"
                    mutations.append((f"bad_type_{prop_name}", payload_bad_type))

                    # minimum boundary violation
                    minimum = prop_schema.get("minimum")
                    if minimum is not None:
                        payload_min = copy.deepcopy(base_payload)
                        payload_min[prop_name] = minimum - 1
                        mutations.append((f"underflow_min_{prop_name}", payload_min))

                    # maximum boundary violation
                    maximum = prop_schema.get("maximum")
                    if maximum is not None:
                        payload_max = copy.deepcopy(base_payload)
                        payload_max[prop_name] = maximum + 1
                        mutations.append((f"overflow_max_{prop_name}", payload_max))

                elif prop_type == "boolean":
                    payload_bad_type = copy.deepcopy(base_payload)
                    payload_bad_type[prop_name] = "not_a_boolean"
                    mutations.append((f"bad_type_{prop_name}", payload_bad_type))

                elif prop_type == "array":
                    payload_bad_type = copy.deepcopy(base_payload)
                    payload_bad_type[prop_name] = "not_an_array"
                    mutations.append((f"bad_type_{prop_name}", payload_bad_type))

                    min_items = prop_schema.get("minItems")
                    if min_items is not None and min_items > 0:
                        payload_underflow = copy.deepcopy(base_payload)
                        payload_underflow[prop_name] = []
                        mutations.append((f"underflow_items_{prop_name}", payload_underflow))

                if "enum" in prop_schema:
                    payload_bad_enum = copy.deepcopy(base_payload)
                    payload_bad_enum[prop_name] = "__INVALID_ENUM_OPTION__"
                    mutations.append((f"invalid_enum_{prop_name}", payload_bad_enum))

        return mutations

    def fuzz_and_validate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mutations and confirm each mutation is rejected by validator."""
        base_payload = self.generate_valid_payload(schema)
        validate_payload(schema, base_payload)

        mutations = self.generate_boundary_mutations(schema)
        results = {
            "valid_payload": base_payload,
            "total_mutations": len(mutations),
            "passed_negatives": 0,
            "details": [],
        }

        for category, mutated in mutations:
            is_rejected = False
            error_msg = ""
            try:
                validate_payload(schema, mutated)
            except SchemaValidationError as exc:
                is_rejected = True
                error_msg = str(exc)

            if is_rejected:
                results["passed_negatives"] += 1

            results["details"].append({
                "category": category,
                "payload": mutated,
                "rejected": is_rejected,
                "error": error_msg,
            })

        return results
