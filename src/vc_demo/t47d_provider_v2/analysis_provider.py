"""Report-only task analyses; the shared engine owns freeze, budgets and credit."""
from vc_demo.t47d_provider_v2.challenges import evaluate


def evaluate_analysis(request):
    if request['phase'] != 'postselection_report_only':
        raise ValueError('Task challenges cannot execute as search feedback')
    return evaluate(request)
