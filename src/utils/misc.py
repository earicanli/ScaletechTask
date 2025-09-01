def walk_depict_dict(d, path=None):

    if path is None:
        path = []

    for k, v in d.items():

        new_path = path + [k]

        # If dict, recurse
        if isinstance(v, dict):
            walk_depict_dict(v, new_path)

        # If list of dicts, recurse first dict
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            print(" -> ".join(new_path))
            print("List of dicts")
            print()
            walk_depict_dict(v[0], new_path)

        # If any other type, print (if feasible)
        else:
            print(" -> ".join(new_path))
            if isinstance(v, str) and len(v) > 100:
                print('String of length > 100')
            else:
                print(v)
            print()
