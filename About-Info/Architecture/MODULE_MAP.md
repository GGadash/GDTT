# Module Map

| Capability | Package | Current state |
|---|---|---|
| Process bootstrap | `app/bootstrap.py` | Implemented |
| Error vocabulary | `domain/errors.py` | Implemented |
| Local settings | `settings/` | Implemented |
| Local logs | `reporting/logging_setup.py` | Implemented |
| Main shell | `ui/main_window.py` | Implemented |
| Themes | `ui/theme.py` | Implemented |
| Home/mode cards | `ui/views/home_view.py`, `ui/widgets/mode_card.py` | Implemented |
| File readers/profiling | `io/` | Implemented |
| Inspection UI/models/workers | `ui/views/inspection_view.py`, `ui/models/`, `ui/workers/` | Implemented |
| Reformat configuration workflow | `app/reformat_configuration.py`, `app/reformat_preview.py` | Phase 5 implemented |
| Reformat mapping/preview UI | `ui/views/configuration_view.py`, `ui/models/configuration_models.py`, `ui/dialogs/column_wizard.py` | Phase 5 implemented |
| Reference and batch/spill table contracts | `domain/table.py`, `domain/batches.py`, `domain/spill.py` | Phase 9 implemented |
| Transformations and recipes | `transformation/` | Implemented |
| Date/time semantics | `datetime/` | Implemented |
| Timezones | `timezone/` | Implemented |
| Gap regularization | `gaps/` | Implemented |
| Aggregation periods/strategies/execution | `aggregation/` | Phase 6 reference plus Phase 9 streamed production execution |
| Averaging configuration/preview composition | `app/averaging_configuration.py`, `app/averaging_preview.py` | Phase 7 implemented |
| Averaging UI/models | `ui/views/averaging_view.py`, `ui/models/averaging_models.py` | Phase 7 implemented |
| Full-file execution/export composition | `io/full_reader.py`, `transformation/batch_executor.py`, `aggregation/batch_engine.py`, `app/export_workflow.py` | Phase 9 batch/spill implemented |
| Data/null validation | `validation/`, `export/verification.py` | Phase 4 plus streamed Phase 9 verification |
| CSV/XLSX writers and naming | `export/` | Phase 8 implemented |
| Processing reports and evidence sidecars | `reporting/processing_report.py` | Phase 8 implemented |
| Recipe templates and XLSX styles | `templates/` | Phase 8 implemented |
| Review/export UI and workers | `ui/views/export_view.py`, `ui/workers/export_worker.py` | Phase 8 implemented |

Use symbols and filenames, not manually maintained line numbers, when locating code.
