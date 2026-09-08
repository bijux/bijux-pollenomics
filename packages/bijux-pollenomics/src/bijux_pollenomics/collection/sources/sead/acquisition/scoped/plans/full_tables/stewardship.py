"""Dataset stewardship, contacts, methods, and bibliography table plans."""

from __future__ import annotations

from ...models import SeadDependency, SeadScopedTablePlan

_STEWARDSHIP_TABLE_PLANS = (
    SeadScopedTablePlan(
        "tbl_dataset_methods",
        "dataset_method_id",
        "dataset_method_id,dataset_id,method_id,date_updated",
        "dataset_id",
        (SeadDependency("tbl_datasets", "dataset_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_dataset_masters",
        "master_set_id",
        (
            "master_set_id,master_set_uuid,master_name,master_notes,biblio_id,"
            "contact_id,url,date_updated"
        ),
        "master_set_id",
        (SeadDependency("tbl_datasets", "master_set_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_dataset_contacts",
        "dataset_contact_id",
        "dataset_contact_id,dataset_id,contact_id,contact_type_id,date_updated",
        "dataset_id",
        (SeadDependency("tbl_datasets", "dataset_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_contacts",
        "contact_id",
        (
            "contact_id,first_name,last_name,address_1,address_2,"
            "phone_number,email,url,date_updated"
        ),
        "contact_id",
        (
            SeadDependency("tbl_dataset_contacts", "contact_id"),
            SeadDependency("tbl_dataset_masters", "contact_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_contact_types",
        "contact_type_id",
        "contact_type_id,contact_type_name,description,date_updated",
        "contact_type_id",
        (SeadDependency("tbl_dataset_contacts", "contact_type_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_methods",
        "method_id",
        "method_id,method_name,method_abbrev_or_alt_name,description",
        "method_id",
        (
            SeadDependency("tbl_relative_dates", "method_id"),
            SeadDependency("tbl_datasets", "method_id"),
            SeadDependency("tbl_dataset_methods", "method_id"),
            SeadDependency("tbl_value_classes", "method_id"),
            SeadDependency("tbl_sample_dimensions", "method_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_biblio",
        "biblio_id",
        "biblio_id,title,full_reference,year,doi,url",
        "biblio_id",
        (
            SeadDependency("tbl_datasets", "biblio_id"),
            SeadDependency("tbl_site_references", "biblio_id"),
            SeadDependency("tbl_sample_group_references", "biblio_id"),
            SeadDependency("tbl_relative_age_refs", "biblio_id"),
            SeadDependency("tbl_dataset_masters", "biblio_id"),
            SeadDependency("tbl_ecocode_systems", "biblio_id"),
        ),
    ),
)
