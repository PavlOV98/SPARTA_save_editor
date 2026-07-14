"""Списки полей, выносимые во вторую секцию (визуальные/текстовые/звуковые)."""

# Поля оружия, которые идут во вторую секцию (после разделителя)
WEAPON_SECONDARY_FIELDS = {
    "itemName", "itemIcon", "itemDescription", "combatItemIcon",
    "emptyIcon", "animatorId", "availableCharacterClass",
    "abilityUseSound", "abilityReloadSound", "abilityReloadFoleySound",
    "showInUI", "stackableInStorage",
}

# Поля предметов (экипировки), которые идут во вторую секцию
ITEM_SECONDARY_FIELDS = {
    "itemName", "itemIcon", "itemDescription", "iconSmall",
}
