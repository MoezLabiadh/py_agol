def overwrite_feature_layer(fc, agol_item_id: str, where_clause: str, unique_id_field: str) -> None:
    """
    Overwrites a feature layer on AGOL by truncating it, then uploading
    each record individually.  Any Poly_Unique_ID that fail to load
    are retried with a 5 m geometry simplification.
    """
    
    print(f"..retrieving target layer with ID: {agol_item_id}")
    item = gis.content.get(agol_item_id)
    if not item:
        raise ValueError(f"Feature layer with ID {agol_item_id} not found.")

    layer = item.layers[0]
    print(f"..found feature layer: {item.title}")

    print("..truncating the feature layer...")
    layer.manager.truncate()
    print("..feature layer truncated successfully.")

    # pick up all non‐OID, non‐Geometry fields
    fields = [
        f.name for f in arcpy.ListFields(fc)
        if f.type not in ("OID", "Geometry")
    ]

    search_fields = ["SHAPE@"] + fields
    failed_ids = []

    print("..uploading records one by one...")
    with arcpy.da.SearchCursor(fc, search_fields, where_clause) as cursor:
        for row in cursor:
            geom = row[0]
            if geom is None:
                print("..skipping record with no geometry")
                continue

            attrs = {fields[i]: row[i + 1] for i in range(len(fields))}
            unique_id = attrs[unique_id_field]

            feature = {
                "geometry": json.loads(geom.JSON),
                "attributes": attrs
            }

            def try_add(feat):
                res = layer.edit_features(adds=[feat])
                add_results = res.get("addResults", [])
                if add_results and add_results[0].get("success", False):
                    return True
                error = add_results[0].get("error", "Unknown error") if add_results else "No result"
                raise RuntimeError(error)

            # first attempt
            try:
                try_add(feature)
                print(f"...successfully added record {unique_id}")
            except Exception as e1:
                print(f"...FAILED to add record {unique_id}: {e1}")
                print(f"...simplifying geometry by 5 m and retrying for {unique_id}")
                # simplify geometry tolerance is in the unit of the spatial reference
                simplified = geom.generalize(5)
                feature["geometry"] = json.loads(simplified.JSON)
                try:
                    try_add(feature)
                    print(f"...successfully added (simplified) {unique_id}")
                except Exception as e2:
                    print(f"...still FAILED after simplification for {unique_id}: {e2}")
                    failed_ids.append(unique_id)

            time.sleep(1)

    if failed_ids:
        print("The following IDs failed even after simplification:")
        for fid in failed_ids:
            print(f" - {fid}")
