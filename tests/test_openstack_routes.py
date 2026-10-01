"""Behavioral tests of the portable coordinator's operational routing."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / 'skills/giga-cloud-learning-guide/scripts/route_openstack.py'


def route(request):
    if not ROUTER.is_file():
        raise AssertionError('portable OpenStack task router missing')
    spec = importlib.util.spec_from_file_location('openstack_router', ROUTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.route(request)


class OperationalRoutingTests(unittest.TestCase):
    def request(self, question, **changes):
        return {'case_id': 'case-17', 'question': question, 'context': {'cloud': 'test-profile', 'project_id': 'project-reference', 'region': 'test-region'}, **changes}

    def test_german_inventory_is_environment_not_new_chapter_journey(self):
        result = route(self.request('Zeige meine OpenStack-VMs und die verbleibende Quota.'))
        self.assertEqual(result['primary_skill'], 'openstack-environment')
        self.assertEqual(result['execution'], 'inspect')
        self.assertEqual(result['case_id'], 'case-17')
        self.assertEqual(result['prior_handoff'], None)

    def test_reachability_question_is_readonly_diagnosis(self):
        result = route(self.request('Warum ist meine VM nicht erreichbar?'))
        self.assertEqual(result['primary_skill'], 'openstack-troubleshooting')
        self.assertEqual(result['execution'], 'inspect')

    def test_volume_growth_prepares_not_executes(self):
        result = route(self.request('Vergrößere mein Datenvolume auf 100 GiB.'))
        self.assertEqual(result['primary_skill'], 'openstack-storage')
        self.assertEqual(result['execution'], 'prepare')
        self.assertFalse(result['mutation_authorized'])

    def test_explicit_execute_without_bound_approval_still_prepares(self):
        result = route(self.request('Execute the VM resize now.', execution='execute'))
        self.assertEqual(result['primary_skill'], 'openstack-compute')
        self.assertEqual(result['execution'], 'prepare')
        self.assertFalse(result['mutation_authorized'])

    def test_no_router_output_ever_authorizes_mutation(self):
        result = route(self.request('Start this VM.', execution='execute', approval='a' * 64))
        self.assertFalse(result['mutation_authorized'])
        self.assertEqual(result['execution'], 'execute-requested')

    def test_capi_owned_compute_routes_to_owner(self):
        result = route(self.request('Resize this OpenStack server.', ownership='capi'))
        self.assertEqual(result['primary_skill'], 'kubernetes-cluster-lifecycle-practitioner')
        self.assertEqual(result['execution'], 'owner-continuation')

    def test_opentofu_owned_target_returns_owner_continuation(self):
        result = route(self.request('Delete the volume.', ownership='opentofu'))
        self.assertEqual(result['execution'], 'owner-continuation')
        self.assertFalse(result['mutation_authorized'])

    def test_network_work_preserves_case_handoff_and_ids(self):
        result = route(self.request('Create a private network and subnet.', prior_handoff={'resource_ids': ['net-17']}))
        self.assertEqual(result['primary_skill'], 'openstack-networking')
        self.assertEqual(result['prior_handoff']['resource_ids'], ['net-17'])

    def test_missing_context_routes_discovery_not_full_baseline(self):
        result = route({'case_id': 'existing', 'question': 'Create a VM.'})
        self.assertEqual(result['primary_skill'], 'openstack-environment')
        self.assertEqual(result['pending_skill'], 'openstack-compute')
        self.assertEqual(result['missing_inputs'], ['cloud', 'project_id', 'region'])

    def test_nonoperational_question_does_not_hijack_cloud_decision(self):
        result = route(self.request('Which delivery model meets our sovereignty requirements?'))
        self.assertEqual(result['status'], 'chapter-route-required')

    def test_unknown_ownership_allows_diagnosis_not_mutation(self):
        result = route(self.request('Why is my VM unreachable?', ownership='unknown'))
        self.assertEqual(result['execution'], 'inspect')

    def test_multi_domain_request_returns_sequence_not_multiple_primary(self):
        result = route(self.request('Create a private network and two VMs, one with a floating IP.'))
        self.assertEqual(result['primary_skill'], 'openstack-networking')
        self.assertIn('openstack-compute', result['continuation_skills'])
        self.assertFalse(result['mutation_authorized'])

    def test_environment_inspection_retains_requested_mutations_in_dependency_order(self):
        result = route(self.request('Inspect quota, then create a private network and a VM.'))
        self.assertEqual(result['primary_skill'], 'openstack-environment')
        self.assertEqual(result['execution'], 'inspect')
        self.assertEqual(result['continuation_skills'], ['openstack-networking', 'openstack-compute'])
        self.assertFalse(result['mutation_authorized'])

    def test_bad_case_input_fails_closed(self):
        with self.assertRaises(ValueError):
            route({'question': 'Delete my VM.'})


    def test_verbatim_question_and_challenge_mode_survive_every_handoff(self):
        question = 'Resize VM MixedCase-ID in RegionOne.'
        for changes in ({}, {'context': None}, {'ownership': 'opentofu'}, {'ownership': 'capi'}, {'execution': 'explain'}):
            with self.subTest(changes=changes):
                result = route(self.request(question, mode='challenge', **changes))
                self.assertEqual(result.get('question'), question)
                self.assertEqual(result.get('mode'), 'challenge')
        result = route(self.request('Which delivery model for ProjectABC?', mode='ask'))
        self.assertEqual(result.get('question'), 'Which delivery model for ProjectABC?')
        self.assertEqual(result.get('mode'), 'ask')


    def test_explicit_inspect_overrides_resize_keywords_and_ownership(self):
        for owner in ('direct', 'opentofu', 'gitops', 'capi'):
            with self.subTest(owner=owner):
                result = route(self.request('Resize this VM.', execution='inspect', ownership=owner))
                self.assertEqual(result['execution'], 'inspect')
                if owner != 'direct':
                    self.assertEqual(result.get('ownership_route'), owner)

    def test_learning_intent_survives_owner_and_discovery_continuations(self):
        for owner in ('opentofu', 'gitops', 'capi'):
            for changes in ({'mode': 'challenge'}, {'execution': 'explain'}, {'mode': 'challenge', 'context': None}):
                with self.subTest(owner=owner, changes=changes):
                    result = route(self.request('Resize this VM.', ownership=owner, **changes))
                    self.assertEqual(result['execution'], 'explain')
                    self.assertEqual(result.get('ownership_route'), owner)
                    self.assertFalse(result['mutation_authorized'])


    def test_context_region_and_profile_do_not_replace_compute_task(self):
        for question in ('Create a VM in region RegionOne.', 'Create VM using profile CloudABC.'):
            with self.subTest(question=question):
                result = route(self.request(question))
                self.assertEqual(result['primary_skill'], 'openstack-compute')
                self.assertEqual(result['execution'], 'prepare')
        result = route(self.request('List regions and profiles.'))
        self.assertEqual(result['primary_skill'], 'openstack-environment')
        self.assertEqual(result['execution'], 'inspect')

    def test_network_vm_volume_creation_keeps_all_domains_in_dependency_order(self):
        for changes in ({}, {'ownership': 'opentofu'}):
            result = route(self.request('Create a private network, a VM and a volume.', **changes))
            self.assertEqual(result['primary_skill'], 'openstack-networking')
            self.assertEqual(result['continuation_skills'], ['openstack-storage', 'openstack-compute'])

    def test_volume_attachment_follows_network_and_compute(self):
        result = route(self.request('Create a private network and VM, then attach a volume.'))
        self.assertEqual(result['primary_skill'], 'openstack-networking')
        self.assertEqual(result['continuation_skills'], ['openstack-compute', 'openstack-storage'])

    def test_ambiguous_volume_dependency_requests_clarification_without_dropping_domains(self):
        result = route(self.request('Create a private network and VM with a volume.'))
        self.assertEqual(result['status'], 'clarification-required')
        self.assertEqual(result['primary_skill'], 'openstack-networking')
        self.assertEqual(set(result['continuation_skills']), {'openstack-compute', 'openstack-storage'})
        self.assertFalse(result['mutation_authorized'])


    def check_missing_field(self, field):
        context = {'cloud': 'CloudABC', 'project_id': 'ProjectXYZ', 'region': 'RegionOne'}
        del context[field]
        for changes in ({}, {'ownership': 'opentofu'}):
            result = route(self.request('Create VM CaseSensitive-ID.', context=context, **changes))
            self.assertEqual(result['missing_inputs'], [field])
            self.assertEqual(result['context'], context)
            self.assertIn(field, result['next_action'])
            for supplied in context:
                self.assertNotIn(supplied, result['next_action'])

    def test_only_missing_cloud_is_requested(self):
        self.check_missing_field('cloud')

    def test_only_missing_project_id_is_requested(self):
        self.check_missing_field('project_id')

    def test_only_missing_region_is_requested(self):
        self.check_missing_field('region')

    def test_partial_context_retains_supplied_case_sensitive_cloud(self):
        context = {'cloud': 'CloudABC'}
        result = route(self.request('Create a VM.', context=context))
        self.assertEqual(result['missing_inputs'], ['project_id', 'region'])
        self.assertEqual(result['context'], context)


if __name__ == '__main__':
    unittest.main()
