# Extension Guide

Introduce extension points only when a second implementation or a clear V1 registry need
exists. Expected registries include readers, writers, transformations, aggregation
strategies, date profiles, missing-value policies, interval alignment, calculated-field
operations, and export styles.

For a new strategy:

1. Define or reuse the smallest UI-independent protocol.
2. Implement one cohesive class/function.
3. Register it through centralized configuration.
4. Test domain behavior without launching Qt.
5. Add UI selection and live-preview adapters separately.
6. Update requirement status, module map, and user documentation.

Do not load arbitrary Python code from recipes and never use unrestricted `eval`.
