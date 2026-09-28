from tests.test_workflows_e2e import (
    test_p0_golden_e2e_and_security_sprint,
    test_pre_hosting_local_hardening_suite,
)


def test_rc1_critical_member_workflow_e2e():
    """
    Runs the complete RC1 critical business flow:
    Member -> Register -> Login -> Profile -> Membership application ->
    Document upload -> Admin review -> Sandbox payment -> Payment verification ->
    Approval -> Membership ID -> Digital ID / QR -> Certificate
    """
    test_p0_golden_e2e_and_security_sprint()
    test_pre_hosting_local_hardening_suite()
