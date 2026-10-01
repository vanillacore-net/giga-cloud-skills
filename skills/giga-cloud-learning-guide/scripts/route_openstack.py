#!/usr/bin/env python3
"""Portable task routing. This helper never authorizes or performs changes."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

SKILLS = {
    'environment': 'openstack-environment',
    'compute': 'openstack-compute',
    'networking': 'openstack-networking',
    'storage': 'openstack-storage',
    'troubleshooting': 'openstack-troubleshooting',
}
PATTERNS = {
    'environment': r'quota|catalogue|catalog|invent[oa]r|bestandsaufnahme|remaining|verbleib|profile|profil|region|\blist\b|\bzeige\b',
    'troubleshooting': r'unreachable|nicht erreichbar|nicht funktioniert|\bfehler\b|diagnos|troubleshoot|why.*(?:vm|server|volume)|warum.*(?:vm|server|volume)|\berror\b',
    'storage': r'volume|datenvolume|storage|snapshot|attachment|block.?speicher|\battach\b|\bdetach\b',
    'networking': r'network|netzwerk|subnet|router|security.?group|sicherheitsgruppe|floating.?ip|\bport\b',
    'compute': r'\bvm\b|\bvms\b|\bserver\b|instance|instanz|flavor|resize|reboot|cloud.?init',
}
MUTATION = r'create|bereitstell|erstell|resize|vergrösser|vergroesser|delete|lösch|loesch|\bstart\b|\bstop\b|reboot|restart|ändern|aender|attach|detach|extend|associate|disassociate|einricht|anleg|verbinde|entfern'
READONLY = r'read.?only|nur lesend|ändere (?:noch )?nichts|aendere (?:noch )?nichts|do not (?:change|modify|apply)|without changes'
SECRET_KEYS = {'password', 'token', 'secret', 'private_key', 'auth_url', 'clouds_yaml', 'kubeconfig_body'}


def check_safe(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in SECRET_KEYS:
                raise ValueError('credential material is not a routing input')
            check_safe(child)
    elif isinstance(value, list):
        for child in value:
            check_safe(child)


def route(request: dict) -> dict:
    if not isinstance(request, dict) or not isinstance(request.get('case_id'), str) or not request['case_id'].strip():
        raise ValueError('case_id is required')
    check_safe(request)
    question = request.get('question', '')
    if not isinstance(question, str) or not question.strip():
        raise ValueError('question is required')
    text = question.casefold()
    domain = request.get('domain')
    if domain is not None and domain not in SKILLS:
        raise ValueError('unsupported domain')
    environment_text = re.sub(r'\b(?:in|using|with)\s+(?:region|profile)\s+[^\s,;.]+', '', text)
    matches = [key for key, pattern in PATTERNS.items()
               if re.search(pattern, environment_text if key == 'environment' else text)]
    if domain:
        selected = domain
    elif 'troubleshooting' in matches:
        selected = 'troubleshooting'
    elif 'environment' in matches:
        selected = 'environment'
    elif 'storage' in matches:
        selected = 'storage'
    elif 'networking' in matches:
        selected = 'networking'
    elif 'compute' in matches:
        selected = 'compute'
    else:
        selected = None
    sequence = []
    ambiguous_dependencies = False
    if selected in {'networking', 'storage', 'compute'} and re.search(MUTATION, text):
        attaching = bool(re.search(r'\battach\b|\bdetach\b|verbinde', text))
        creating = bool(re.search(r'create|erstell|anleg|bereitstell', text))
        if 'storage' in matches and 'compute' in matches:
            ambiguous_dependencies = not attaching and (not creating or bool(re.search(r'with (?:a |an |the )?volume', text)))
        order = ('networking', 'compute', 'storage') if attaching or ambiguous_dependencies else ('networking', 'storage', 'compute')
        sequence = [key for key in order if key in matches or key == selected]
        selected = sequence[0]
    if selected == 'environment' and re.search(MUTATION, text):
        sequence = ['environment'] + [key for key in ('networking', 'storage', 'compute') if key in matches]
    result = {
        'schema': 'openstack-routing-record/v1',
        'case_id': request['case_id'],
        'question': question,
        'mode': request.get('mode'),
        'primary_skill': SKILLS.get(selected or ''),
        'pending_skill': None,
        'domain': selected,
        'execution': 'inspect',
        'mutation_authorized': False,
        'prior_handoff': request.get('prior_handoff'),
        'context': request.get('context'),
        'continuation_skills': [SKILLS[key] for key in sequence[1:]],
        'missing_inputs': [],
        'status': 'focused-skill-required' if selected else 'chapter-route-required',
        'next_action': 'Activate the named installed skill; this record is not change approval.',
    }
    if not selected:
        return result
    mutating = bool(re.search(MUTATION, text)) and selected not in {'environment', 'troubleshooting'}
    readonly = bool(re.search(READONLY, text))
    execution = request.get('execution')
    if execution not in (None, 'explain', 'prepare', 'execute', 'inspect'):
        raise ValueError('unsupported execution intent')
    if request.get('mode') in {'ask', 'learn', 'challenge', 'review'} or execution == 'explain':
        result['execution'] = 'explain'
    elif execution == 'inspect':
        result['execution'] = 'inspect'
    elif mutating and not readonly:
        result['execution'] = 'prepare'
        if execution == 'execute' and isinstance(request.get('approval'), str) and re.fullmatch(r'[0-9a-f]{64}', request['approval']):
            result['execution'] = 'execute-requested'
            result['next_action'] = 'Focused runtime must verify the exact saved plan digest, target, freshness and ownership before executing.'
    if ambiguous_dependencies:
        result.update(status='clarification-required', next_action='Clarify whether the volume must be created before VM provisioning or attached after it; all requested domains are retained.')
    owner = request.get('ownership', 'unknown')
    if owner not in {'direct', 'unknown', 'opentofu', 'capi', 'gitops'}:
        raise ValueError('unsupported ownership')
    if owner in {'opentofu', 'gitops', 'capi'}:
        result['ownership_route'] = owner
        if result['execution'] in {'prepare', 'execute-requested'} and not ambiguous_dependencies:
            if owner == 'capi':
                result['primary_skill'] = 'kubernetes-cluster-lifecycle-practitioner'
            result.update(execution='owner-continuation', next_action='Use the supplied owning declaration and its plan or diff; direct OpenStack mutation is blocked.')
    context = request.get('context')
    result['missing_inputs'] = [key for key in ('cloud', 'project_id', 'region')
                                if not isinstance(context, dict) or not context.get(key)]
    if result['missing_inputs']:
        if selected != 'environment':
            result.update(pending_skill=result['primary_skill'], primary_skill='openstack-environment', domain='environment')
            if result['execution'] in {'prepare', 'execute-requested'}:
                result['execution'] = 'inspect'
        result['next_action'] = ('Discover or request only missing inputs: '
                                 + ', '.join(result['missing_inputs'])
                                 + '; then resume the pending task with its preserved intent and ownership route. No new chapter architecture decision is required.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = route(json.loads(args.request.read_text(encoding='utf-8')))
    except (OSError, ValueError):
        print(json.dumps({'status': 'blocked', 'reason': 'invalid or unsafe routing input'}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
