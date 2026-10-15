# SevaSetu AI — Automated Test Report

Generated: 2026-10-13 19:39  
Database used: `sevasetu_test_db` (PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1), PostGIS 3.4.2)  
AI detector in these tests: **fake stand-in objects** (no model weights loaded)  
Result: **77/77 passed** (0 failed/skipped), total time 24.2 s

Tests run against a real PostgreSQL + PostGIS database through the FastAPI test client. Route tests of the AI pipeline use a stand-in detector; real model performance is reported separately (see AI evaluation).

## Summary by area

| Area | Tests | Passed |
|---|---|---|
| Authentication & issue reporting | 7 | 7 |
| Priority engine & AI integration | 11 | 11 |
| Duplicate detection & authority workflow | 13 | 13 |
| Hotspots, analytics & resolution workflow | 13 | 13 |
| System robustness & error handling | 19 | 19 |
| Evaluation harness & demo data | 7 | 7 |
| AI with/without weights (fake detectors) | 7 | 7 |

## All tests

| Area | Test | Result | Time (s) |
|---|---|---|---|
| AI with/without weights (fake detectors) | `test_real_detector_reports_unavailable_when_weights_missing` | PASS | 0.07 |
| AI with/without weights (fake detectors) | `test_no_weights_means_no_detection_and_manual_category_works` | PASS | 0.75 |
| AI with/without weights (fake detectors) | `test_inference_crash_is_swallowed_not_fatal` | PASS | 0.59 |
| AI with/without weights (fake detectors) | `test_unmapped_class_is_ignored_even_at_high_confidence` | PASS | 0.56 |
| AI with/without weights (fake detectors) | `test_mapped_class_wins_over_higher_confidence_unmapped_class` | PASS | 0.00 |
| AI with/without weights (fake detectors) | `test_mapped_detection_drives_category_severity_and_prediction_row` | PASS | 0.58 |
| AI with/without weights (fake detectors) | `test_user_category_overrides_ai_but_prediction_is_kept` | PASS | 0.59 |
| Authentication & issue reporting | `test_duplicate_email_rejected` | PASS | 0.55 |
| Authentication & issue reporting | `test_wrong_password` | PASS | 0.28 |
| Authentication & issue reporting | `test_requires_auth` | PASS | 0.01 |
| Authentication & issue reporting | `test_create_and_fetch_issue` | PASS | 0.08 |
| Authentication & issue reporting | `test_invalid_inputs` | PASS | 0.07 |
| Authentication & issue reporting | `test_citizen_cannot_view_others_issue` | PASS | 0.56 |
| Authentication & issue reporting | `test_authority_can_view_any_issue` | PASS | 0.30 |
| Priority engine & AI integration | `test_blueprint_example_scores_81_25` | PASS | 0.00 |
| Priority engine & AI integration | `test_weights_sum_to_one` | PASS | 0.00 |
| Priority engine & AI integration | `test_frequency_and_time_scores` | PASS | 0.00 |
| Priority engine & AI integration | `test_location_keywords` | PASS | 0.00 |
| Priority engine & AI integration | `test_severity_levels` | PASS | 0.00 |
| Priority engine & AI integration | `test_ai_status_without_weights` | PASS | 0.60 |
| Priority engine & AI integration | `test_no_type_and_no_ai_is_rejected` | PASS | 0.01 |
| Priority engine & AI integration | `test_manual_type_without_ai_gets_default_severity` | PASS | 0.03 |
| Priority engine & AI integration | `test_ai_detects_type_and_scores_priority` | PASS | 0.03 |
| Priority engine & AI integration | `test_user_type_wins_but_prediction_is_kept` | PASS | 0.03 |
| Priority engine & AI integration | `test_analyze_preview_endpoint` | PASS | 0.01 |
| Duplicate detection & authority workflow | `test_reports_within_25m_merge_into_one_issue` | PASS | 1.80 |
| Duplicate detection & authority workflow | `test_different_category_does_not_merge` | PASS | 0.66 |
| Duplicate detection & authority workflow | `test_far_report_is_a_separate_issue` | PASS | 0.64 |
| Duplicate detection & authority workflow | `test_citizen_cannot_see_duplicate_review_data` | PASS | 0.95 |
| Duplicate detection & authority workflow | `test_authority_confirms_duplicate_merge` | PASS | 0.75 |
| Duplicate detection & authority workflow | `test_authority_dismisses_duplicate` | PASS | 0.71 |
| Duplicate detection & authority workflow | `test_citizen_blocked_from_admin_endpoints` | PASS | 0.61 |
| Duplicate detection & authority workflow | `test_dashboard_kpis_are_consistent` | PASS | 0.07 |
| Duplicate detection & authority workflow | `test_issue_list_filters_and_sorting` | PASS | 0.86 |
| Duplicate detection & authority workflow | `test_full_status_workflow` | PASS | 0.87 |
| Duplicate detection & authority workflow | `test_reopen_clears_resolved_at` | PASS | 0.80 |
| Duplicate detection & authority workflow | `test_departments_list` | PASS | 0.01 |
| Duplicate detection & authority workflow | `test_unknown_issue_404` | PASS | 0.01 |
| Hotspots, analytics & resolution workflow | `test_haversine_known_distance` | PASS | 0.00 |
| Hotspots, analytics & resolution workflow | `test_dbscan_finds_cluster_and_ignores_noise` | PASS | 0.00 |
| Hotspots, analytics & resolution workflow | `test_chain_connects_through_density` | PASS | 0.00 |
| Hotspots, analytics & resolution workflow | `test_two_separate_clusters` | PASS | 0.00 |
| Hotspots, analytics & resolution workflow | `test_hotspot_summary_fields` | PASS | 0.00 |
| Hotspots, analytics & resolution workflow | `test_too_few_points_no_hotspot` | PASS | 0.00 |
| Hotspots, analytics & resolution workflow | `test_map_endpoint_detects_hotspot` | PASS | 1.00 |
| Hotspots, analytics & resolution workflow | `test_map_requires_authority` | PASS | 0.64 |
| Hotspots, analytics & resolution workflow | `test_analytics_trend` | PASS | 0.64 |
| Hotspots, analytics & resolution workflow | `test_resolve_with_after_photo_and_verify` | PASS | 0.74 |
| Hotspots, analytics & resolution workflow | `test_rejected_resolution_reopens_issue` | PASS | 0.69 |
| Hotspots, analytics & resolution workflow | `test_resolve_rejects_bad_photo_and_wrong_state` | PASS | 0.71 |
| Hotspots, analytics & resolution workflow | `test_citizen_cannot_resolve_or_verify` | PASS | 0.58 |
| Evaluation harness & demo data | `test_summary_math` | PASS | 0.00 |
| Evaluation harness & demo data | `test_latency_stats_and_markdown` | PASS | 0.00 |
| Evaluation harness & demo data | `test_collect_reads_folder_labels` | PASS | 0.00 |
| Evaluation harness & demo data | `test_demo_plan_is_deterministic_and_sized` | PASS | 0.00 |
| Evaluation harness & demo data | `test_demo_hero_scenario` | PASS | 0.00 |
| Evaluation harness & demo data | `test_demo_data_yields_exactly_three_named_hotspots` | PASS | 0.00 |
| Evaluation harness & demo data | `test_demo_spacing_and_status_mix` | PASS | 0.00 |
| System robustness & error handling | `test_bad_tokens_are_rejected` | PASS | 0.03 |
| System robustness & error handling | `test_protected_routes_need_a_token[/api/auth/me]` | PASS | 0.01 |
| System robustness & error handling | `test_protected_routes_need_a_token[/api/issues/my]` | PASS | 0.01 |
| System robustness & error handling | `test_protected_routes_need_a_token[/api/issues/1]` | PASS | 0.01 |
| System robustness & error handling | `test_protected_routes_need_a_token[/api/ai/status]` | PASS | 0.00 |
| System robustness & error handling | `test_protected_routes_need_a_token[/api/admin/dashboard]` | PASS | 0.01 |
| System robustness & error handling | `test_protected_routes_need_a_token[/api/admin/issues]` | PASS | 0.01 |
| System robustness & error handling | `test_protected_routes_need_a_token[/api/admin/map]` | PASS | 0.01 |
| System robustness & error handling | `test_protected_routes_need_a_token[/api/admin/analytics]` | PASS | 0.01 |
| System robustness & error handling | `test_register_validation_and_no_privilege_escalation` | PASS | 0.30 |
| System robustness & error handling | `test_report_input_validation` | PASS | 0.60 |
| System robustness & error handling | `test_oversized_image_rejected` | PASS | 0.63 |
| System robustness & error handling | `test_non_image_and_empty_uploads_rejected` | PASS | 0.59 |
| System robustness & error handling | `test_pagination_bounds_enforced` | PASS | 0.34 |
| System robustness & error handling | `test_sql_injection_in_search_is_inert` | PASS | 0.38 |
| System robustness & error handling | `test_uploads_path_traversal_blocked` | PASS | 0.01 |
| System robustness & error handling | `test_markup_in_description_is_returned_as_plain_data` | PASS | 0.60 |
| System robustness & error handling | `test_same_citizen_double_submit_merges_instead_of_duplicating` | PASS | 0.65 |
| System robustness & error handling | `test_missing_location_message_is_clear` | PASS | 0.59 |
