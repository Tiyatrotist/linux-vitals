from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULTS = REPO_ROOT / "roles" / "vitals_report" / "defaults" / "main.yml"
MAIN = REPO_ROOT / "roles" / "vitals_report" / "tasks" / "main.yml"
GATE = REPO_ROOT / "roles" / "vitals_report" / "tasks" / "gate.yml"


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_fleet_gate_is_opt_in_by_default():
    defaults = load_yaml(DEFAULTS)

    assert defaults["linux_vitals_fail_on_status"] == ""
    assert defaults["linux_vitals_fail_threshold_count"] == 0


def test_fleet_gate_runs_after_notifications():
    tasks = load_yaml(MAIN)
    included = [task["ansible.builtin.include_tasks"]["file"] for task in tasks]

    assert included[-2:] == ["notify.yml", "gate.yml"]


def test_fleet_gate_supports_any_fail_regression_and_threshold():
    tasks = load_yaml(GATE)

    validation = tasks[0]["ansible.builtin.assert"]["that"]
    assert "linux_vitals_fail_on_status in ['', 'any_fail', 'regression']" in validation

    count_expression = tasks[1]["ansible.builtin.set_fact"]["linux_vitals_gate_failure_count"]
    assert "linux_vitals_summary.critical_error_count" in count_expression
    assert "linux_vitals_summary.regressed_count" in count_expression
    assert "linux_vitals_phase == 'postcheck'" in count_expression

    conditions = tasks[2]["when"]
    assert any("linux_vitals_gate_failure_count" in condition for condition in conditions)
    assert any("linux_vitals_fail_threshold_count" in condition for condition in conditions)
