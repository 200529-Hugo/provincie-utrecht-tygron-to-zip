import unittest

from scenario_dossier.web import _item_inventory, _select_data


class ItemSelectionTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "overlays": [
                {"id": 1, "name": "Heat"},
                {"id": 2, "name": "Water"},
            ],
            "indicators": [{"id": 3, "name": "Green", "value": 72, "unit": "%"}],
            "measures": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [5.1, 52.1]},
                "properties": {"id": 4, "name": "Park"},
            }],
            "alerts": [{"name": "Zonder id"}],
        }

    def test_inventory_has_stable_keys_and_spatial_flag(self):
        inventory = _item_inventory(self.data)

        self.assertEqual([item["key"] for item in inventory], [
            "id:1", "id:2", "id:3", "id:4", "index:0",
        ])
        self.assertTrue(next(item for item in inventory if item["key"] == "id:4")["spatial"])

    def test_selection_filters_individual_items(self):
        selected = _select_data(
            self.data,
            ["overlays", "measures"],
            {"overlays": ["id:2"], "measures": ["id:4"]},
        )

        self.assertEqual([item["name"] for item in selected["overlays"]], ["Water"])
        self.assertEqual(len(selected["measures"]), 1)
        self.assertEqual(selected["indicators"], [])
        self.assertEqual(selected["alerts"], [])


if __name__ == "__main__":
    unittest.main()
