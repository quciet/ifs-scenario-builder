import json
import unittest
from scenario_compiler import References
from scenario_research import preflight, provider_view, numeric_clarification_issue
from scenario_intelligence import semantic_entries, narrative_direction


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.refs=References({'govcorruptm':(1,0,0),'migrateinm':(1,0,0),'econfreem':(1,0,0),'goveffectm':(1,0,0)},
            {},{'Iraq','Jordan'},metadata={'govcorruptm':{'UNITS':'Multiplier'}})

    def test_metadata_preserves_inverse_polarity_and_preloads_followups(self):
        facts=preflight('Use govcorruptm and econfreem.',self.refs,{})
        self.assertEqual(facts['verified']['govcorruptm']['interpretation']['semantic_rule']['polarity'],-1)
        self.assertIn('econfreem',facts['verified'])

    def test_meaning_conflict_is_specific_to_explicit_label(self):
        facts=preflight('Less economic freedom (goveffectm).',self.refs,{'goveffectm':'Government effectiveness','econfreem':'Economic freedom'})
        self.assertEqual(facts['meaning_conflicts'][0]['candidate'],'econfreem')

    def test_same_parameter_opposite_country_directions_are_independent(self):
        entries=[{'parameter':'migrateinm','targets':['Iraq'],'values':[1,1.1],
                  'effect':{'direction':'increase'}},
                 {'parameter':'migrateinm','targets':['Jordan'],'values':[1,.9],
                  'effect':{'direction':'decrease'}}]
        result,receipts=semantic_entries(entries,self.refs,'',base_year=2022)
        self.assertEqual(len(result),2)
        self.assertEqual([r['direction'] for r in receipts],['increase','decrease'])

    def test_opposite_scoped_phrases_do_not_become_a_global_last_phrase_rule(self):
        self.assertIsNone(narrative_direction('govcorruptm',['Iraq'],self.refs,
            'More corruption in Iraq. Less corruption in Jordan.'))

    def test_group_receipts_compact_without_losing_target_values(self):
        rows=[{'parameter':'govcorruptm','targets':[c],'source':'same/path','baseline':'1','endpoint':'.9'} for c in self.refs.countries]
        original=[{'role':'tool','content':json.dumps({'parameter':'govcorruptm','suggestions':rows})}]
        result=json.loads(provider_view(original)[0]['content'])
        self.assertEqual(len(result['suggestion_groups']),1)
        self.assertEqual({tuple(t) for t in result['suggestion_groups'][0]['targets']},{('Iraq',),('Jordan',)})
        self.assertIn('suggestions',json.loads(original[0]['content']))

    def test_unvalidated_numeric_suggestions_do_not_escape_direction_check(self):
        self.assertIsNotNone(numeric_clarification_issue('Use govcorruptm at 1.10.', 'More corruption.', self.refs))
        self.assertIsNone(numeric_clarification_issue('Use govcorruptm at 1.10.', 'Please use 1.10.', self.refs))
