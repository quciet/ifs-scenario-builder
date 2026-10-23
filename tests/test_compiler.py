import tempfile
import unittest
from pathlib import Path
from scenario_compiler import Compiler, References, ValidationError


EXPORT = dict(purpose='Increase the scalar parameter gradually.', regeneration_prompt='Increase scalar linearly over the scenario horizon.', model_context={'version': 'test', 'base_year': 2022})


class CompilerTests(unittest.TestCase):
    def setUp(self):
        self.compiler = Compiler(References(
            {'scalar': (0, 0, 0), 'country': (1, 0, 0),
             'sector': (2, 0, 0), 'cube': (1, 2, 3), 'later': (0, 2, 0)},
            {2: {1: 'Agriculture'}, 3: {4: 'Example'}}, {'Exact Country'}))

    def test_ragged_dimensions_and_csv_roundtrip(self):
        rows = self.compiler.build([
            {'parameter': 'scalar', 'values': [1, 2]},
            {'parameter': 'country', 'targets': ['Exact Country'], 'values': [3]},
            {'parameter': 'sector', 'targets': [1], 'values': [4]},
            {'parameter': 'cube', 'targets': ['Exact Country', 1, 4], 'values': [5]},
            {'parameter': 'later', 'targets': [1], 'values': [6]}])
        self.assertEqual(rows[0], ['CUSTOM', 'scalar', '1', '2'])
        self.assertEqual(rows[3], ['CUSTOM', 'cube', 'Exact Country', '1', '4', '5'])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'new.sce'
            self.compiler.save(rows, path, **EXPORT)
            self.assertEqual(self.compiler.read(path), rows)
            with self.assertRaises(ValidationError):
                self.compiler.save(rows, path, **EXPORT)

    def test_exact_years_and_preservation(self):
        rows = [['HEADER', 'example'], ['CUSTOM', 'scalar', '1', '2', '3']]
        changes = [{'parameter': 'scalar', 'start_year': 2023, 'end_year': 2024,
                    'operation': 'multiply', 'value': '1.5'}]
        changed = self.compiler.modify(rows, changes)
        self.assertEqual(changed[1], ['CUSTOM', 'scalar', '1', '3.0', '4.5'])
        self.assertEqual(rows[1][-1], '3')
        self.assertEqual(changed[0], rows[0])
        for operation, expected in [('add', '4'), ('zero', '0')]:
            changes[0].update(operation=operation, value=2)
            self.assertEqual(self.compiler.modify(rows, changes)[1][3], expected)

    def test_reject_unknown_targets_and_numbers(self):
        for entry in [
            {'parameter': 'invented', 'values': [1]},
            {'parameter': 'country', 'targets': ['exact country'], 'values': [1]},
            {'parameter': 'sector', 'targets': [99], 'values': [1]},
            {'parameter': 'cube', 'targets': ['Exact Country'], 'values': [1]},
            {'parameter': 'scalar', 'values': ['NaN']}]:
            with self.subTest(entry=entry), self.assertRaises(ValidationError):
                self.compiler.build([entry])

    def test_reject_missing_target_and_out_of_range(self):
        rows = [['CUSTOM', 'scalar', '1']]
        for start in [2021, 2023]:
            with self.assertRaises(ValidationError):
                self.compiler.modify(rows, [{'parameter': 'scalar', 'start_year': start,
                    'end_year': start, 'operation': 'zero'}])

    def test_native_reference_integration(self):
        folder = Path(__file__).resolve().parents[2] / 'Docs' / 'Gem-Jonathan'
        if not folder.is_dir():
            self.skipTest('Optional local Docs/Gem-Jonathan references are unavailable')
        refs = References.load(folder / 'IFsVar.txt', folder / 'IFS.grp',
                               folder / 'country names for sce files.txt')
        self.assertEqual(len(refs.countries), 188)
        self.assertEqual(refs.dimensions('actreaon'), (0, 0, 0))
        self.assertEqual(refs.targets('inputagrim', ['Afghanistan', 'Agriculture']),
                         ['Afghanistan', '1'])
        self.assertEqual(refs.targets('edqualag15m', ['Afghanistan', 'Female']),
                         ['Afghanistan', '2'])
        self.assertEqual(refs.groups[58][1], 'Agriculture')
        with self.assertRaises(ValidationError):
            refs.dimensions('HHSAVSTOCK')
        compiler = Compiler(refs)
        rows = compiler.build([
            {'parameter': 'actreaon', 'values': [1, 1, 1]},
            {'parameter': 'inputagrim', 'targets': ['Afghanistan', 'Agriculture'],
             'values': [1, 1.1, 1.2]}])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'verified.sce'
            compiler.save(rows, path, **EXPORT)
            loaded = compiler.read(path)
            changed = compiler.modify(loaded, [{'parameter': 'inputagrim',
                'targets': ['Afghanistan', 1], 'start_year': 2023,
                'end_year': 2024, 'operation': 'multiply', 'value': 2}])
            self.assertEqual(changed[1][-3:], ['1', '2.2', '2.4'])

    def test_mandatory_descriptive_metadata(self):
        rows = self.compiler.build([{'parameter': 'scalar', 'values': ['1.00', '2.25']}])
        text = self.compiler.render(rows, **EXPORT)
        self.assertEqual(text.count('COMMENT,START'), 1)
        self.assertIn('Created:', text)
        self.assertIn('(UTC)', text)
        comment = text.split('COMMENT,START\n')[1]
        self.assertIn('Parameters used: scalar.', comment)
        self.assertNotIn('Structured specification', comment)
        self.assertNotIn('2.25', comment)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'missing.sce'
            with self.assertRaises(ValidationError):
                self.compiler.save(rows, path, **{**EXPORT, 'purpose': ''})
            self.assertFalse(path.exists())

    def test_comments_are_opaque_and_preserved_when_modified(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.sce'
            comments = 'Unmatched "quote, and comma\nCUSTOM,invented,not data\nOriginal intent.\n'
            source.write_text('CUSTOM,scalar,1,2\nCOMMENT,START\n' + comments, newline='')
            rows = self.compiler.read(source)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows.comments, comments)
            changed = self.compiler.modify(rows, [{'parameter': 'scalar', 'start_year': 2023,
                'end_year': 2023, 'operation': 'zero'}])
            output = Path(folder) / 'flavor.sce'
            self.compiler.save(changed, output, **EXPORT)
            text = output.read_text()
            self.assertIn(comments, text)
            self.assertIn('Source scenario: source.sce', text)
            self.assertEqual(self.compiler.read(output)[0][-1], '0')


if __name__ == '__main__':
    unittest.main()
