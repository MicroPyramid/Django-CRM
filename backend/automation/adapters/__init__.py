"""One `automation.objects.Adapter` per built-in object rules can automate."""


def same_org(record, column):
    """The record `column` points at, unless it is empty or outside the record's org.

    The parent is looked up by id and org, never through the relation, which
    raises when row-level security hides the row.
    """
    parent_id = getattr(record, f"{column}_id")
    if parent_id is None:
        return None
    model = record._meta.get_field(column).related_model
    return model.objects.filter(pk=parent_id, org_id=record.org_id).first()
