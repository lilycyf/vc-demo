"""Applicability is different from module consumption and scientific benefit."""


def control_verdict(*, removed_roles, consumed_roles, changed_dependency_identity, removed_roles_still_consumed):
    targeted=set(removed_roles)&set(consumed_roles)
    if not targeted:
        return {'applicability':'not_applicable','control_applied':False,
            'reason':'The original model did not consume the removed module; equal scores do not validate it.'}
    applied=bool(changed_dependency_identity and not (targeted&set(removed_roles_still_consumed)))
    return {'applicability':'applicable','control_applied':applied,
        'reason':'Dependency removal verified; performance change still needs paired evaluation.' if applied
                 else 'The intended intervention was not verified; do not infer module usefulness.'}
