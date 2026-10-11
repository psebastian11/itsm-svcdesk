---
lab3_genai_diff:
  instrumentation: "opentelemetry-sdk 1.45.0 (manual OTLP span example)"
  spec_ref: semantic-conventions@v1.41.1
  attributes:
    - {name: gen_ai.operation.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.provider.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.id, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.input_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.output_tokens, emitted: true, in_spec: true, stability: development}
---
<!-- ai-generated: 100% - attributes compared with the v1.41.1 GenAI registry -->

# What the span records against the spec

This OTLP span is a manually constructed OpenAI-compatible chat example, not a captured provider call or output
from an auto-instrumentation package. No API key or external model request was used. The seven GenAI attributes
in the span are all defined in `semantic-conventions@v1.41.1`; each is marked `development` in that registry.

The request model and operation name describe the call, while the response model and id describe the result.
The token counts record input and output usage separately. Because this example supplies every declared field
directly, it demonstrates the semantic-convention shape but does not demonstrate which fields a particular
OpenAI instrumentation library emits or whether that library omits attributes.
