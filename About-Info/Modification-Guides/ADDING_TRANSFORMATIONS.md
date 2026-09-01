# Adding Transformations

Add a transformation by subclassing `TransformationOperation`, returning `OperationResult`,
and keeping its configuration immutable. Add the matching inert `TransformationSpec` recipe
shape, before/after preview adapter when the UI phase arrives, and valid/null/invalid tests.
Use `Diagnostic` for counted non-blocking outcomes and `TransformationError` for explicit stop
conditions. Never accept unrestricted expressions or place calculation in a Qt signal handler.
