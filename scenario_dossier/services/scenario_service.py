from __future__ import annotations

from collections.abc import Iterable, Mapping

from ..models import ComponentType, ScenarioData, ScenarioItem


class ScenarioService:
    def inventory(self, data: ScenarioData) -> list[ScenarioItem]:
        inventory: list[ScenarioItem] = []
        for component in ComponentType:
            inventory.extend(
                ScenarioItem.from_raw(component, raw, index)
                for index, raw in enumerate(data.items(component))
            )
        return inventory

    def select(
        self,
        data: ScenarioData,
        selected_components: Iterable[str] | None = None,
        selected_items: Mapping[str, Iterable[str]] | None = None,
    ) -> ScenarioData:
        component_names = (
            set(ComponentType.values())
            if selected_components is None
            else {str(name) for name in selected_components}
        )
        unknown = component_names.difference(ComponentType.values())
        if unknown:
            raise ValueError(f"Onbekende scenario-onderdelen: {', '.join(sorted(unknown))}")

        item_selection = selected_items or {}
        result: dict[str, list[dict]] = {}
        for component in ComponentType:
            name = component.value
            items = data.items(component) if name in component_names else []
            if name in item_selection:
                wanted = {str(key) for key in item_selection[name]}
                items = [
                    raw
                    for index, raw in enumerate(items)
                    if ScenarioItem.from_raw(component, raw, index).key in wanted
                ]
            result[name] = list(items)
        return ScenarioData.from_dict(result)
