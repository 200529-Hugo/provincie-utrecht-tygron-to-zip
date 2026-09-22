import tempfile
import unittest
from pathlib import Path

from scenario_dossier.models import (
    ComponentType,
    DossierDetails,
    ScenarioData,
)
from scenario_dossier.services import (
    DemoService,
    DossierService,
    ScenarioService,
    ValidationService,
)


class ModelTests(unittest.TestCase):
    def test_scenario_data_has_all_supported_components(self):
        data = ScenarioData.from_dict({"measures": [{"id": 1}]})

        self.assertEqual(data.counts(), {
            "overlays": 0,
            "indicators": 0,
            "measures": 1,
            "alerts": 0,
        })
        self.assertEqual(data.items(ComponentType.MEASURES), [{"id": 1}])

    def test_dossier_details_normalizes_input(self):
        details = DossierDetails.from_dict({"reference": "  PU-42  ", "owner": 12})

        self.assertEqual(details.reference, "PU-42")
        self.assertEqual(details.owner, "12")


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.demo_service = DemoService()
        self.scenario_service = ScenarioService()

    def test_demo_service_returns_domain_models(self):
        projects = self.demo_service.list_projects()
        scenario = self.demo_service.get_scenario(
            projects[0].id,
            projects[0].scenarios[0].id,
        )

        self.assertTrue(projects)
        self.assertTrue(scenario.name)
        self.assertGreater(scenario.data.total_count(), 0)
        self.assertNotIn("data", projects[0].to_public_dict()["scenarios"][0])

    def test_scenario_service_creates_inventory_and_selection(self):
        data = ScenarioData.from_dict({
            "overlays": [
                {"id": 1, "name": "Hitte"},
                {"id": 2, "name": "Water"},
            ],
            "measures": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [5.1, 52.1]},
                "properties": {"id": 3, "name": "Park"},
            }],
        })

        inventory = self.scenario_service.inventory(data)
        selected = self.scenario_service.select(
            data,
            selected_components=["overlays", "measures"],
            selected_items={"overlays": ["id:2"], "measures": ["id:3"]},
        )

        self.assertEqual([item.key for item in inventory], ["id:1", "id:2", "id:3"])
        self.assertTrue(inventory[-1].spatial)
        self.assertEqual(selected.overlays, [{"id": 2, "name": "Water"}])
        self.assertEqual(len(selected.measures), 1)
        self.assertEqual(selected.indicators, [])

    def test_dossier_and_validation_services_return_models(self):
        project = self.demo_service.list_projects()[0]
        scenario = project.scenarios[0]

        with tempfile.TemporaryDirectory() as temporary_directory:
            dossier_service = DossierService(Path(temporary_directory))
            archive = dossier_service.create(
                project.name,
                scenario.name,
                scenario.data,
                details=DossierDetails(reference="PU-TEST-1"),
            )
            validation = ValidationService().validate_archive(archive.path)

        self.assertTrue(archive.filename.endswith(".zip"))
        self.assertGreater(archive.size, 0)
        self.assertTrue(validation.approved)


if __name__ == "__main__":
    unittest.main()
