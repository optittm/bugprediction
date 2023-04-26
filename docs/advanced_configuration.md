# Advanced configuration

## Include and exclude file from your project

### Simple configuration

The simple configuration allows you to include or exclude a list of folder by setting the ```OTTM_INCLUDE_FOLDERS``` or ```OTTM_EXCLUDE_FOLDERS``` environment variable in your .env file. The value of these variables should be a comma-separated list of folder paths.

Example:

```
OTTM_INCLUDE_FOLDERS=path/to/folder1,path/to/folder2
OTTM_EXCLUDE_FOLDERS=path/to/excluded/folder
```

### Advanced configuration

The advanced configuration allows you to specify a more precise configuration using a JSON format. This format allows you to define folder paths for specific versions of your project. The configuration should be formatted like this:

```json
{
    "<=1.0.0": [
        "path/to/folder1", 
        "path/to/folder2"
        ],
    ">=1.0.1": [
        "path/to/folder3"
        ],
    "*": ["path/to/folder4"]
}
```

The operators that can be used in the configuration are ==, !=, <=, >=, <, > and *. The * operator means all versions without restriction.

In the example above, the first entry specifies that for versions less than or equal to 1.0.0, the folders "path/to/folder1" and "path/to/folder2" should be included. The second entry specifies that for versions greater than or equal to 1.0.1, the folder "path/to/folder3" should be included. The third entry specifies that for all other versions, the folder "path/to/folder4" should be included.

#### The `==` Operator

The `==` operator can be used to add exceptions to a rule. For example, if the configuration is:

```json
{
    ">=1.0.0": ["path_1"],
    "==1.5.0": ["path_2"]
}
```

Then for all versions greater than or equal to 1.0.0, the restriction will be `["path_1"]` except for version 1.5.0, which will have the restriction `["path_2"]`.

#### The `!=` Operator

The `!=` operator is the exact opposite of the `==` operator. For example, if the configuration is:

```json
{
    ">=1.0.0": ["path_1"],
    "!=1.5.0": ["path_2"]
}
```

Then for all versions greater than or equal to 1.0.0, the restriction will be `["path_2"]` except for version 1.5.0, which will have the restriction `["path_1"]`.

#### The `*` Operator

The `*` operator matches any version without restriction. For example, if the configuration is:

```json
{
    "*": ["path_1"],
    ">1.0.0": ["path_2"]
}
```

Then the restriction for all version under 1.0.0 will be `["path_2"]` and it will be `["path_1"]` for all other version. Note that if there are other rules with version restrictions, the `*` operator will not apply to those versions.

Note that if the `*` operator is not specified in the configuration, there will be no default restriction applied to versions that are not covered by other rules. In this case, any version that is not covered by a rule will not have any restrictions applied to it and all folders will be used.

#### Handling Conflicts

In case of conflicts between rules for the same version, the lower version rule will be ignored. For example, if the configuration is:

```json
{
    "<=2.0.0": ["path_2"],
    ">=1.0.0": ["path_1"]
}
```

Then the restriction applied to the versions between 1.0.0 and 2.0.0 will be `["path_2"]`.

Note that this behavior also applies to conflicting rules with different operators. For example, if the configuration is:

```json
{
    "<1.0.0": ["path_1"],
    "<1.5.0": ["path_2"]
}
```

Then for version 0.5.0, the restriction will be `["path_1"]`.

Similarly, if the configuration is:

```json
{
    ">1.0.0": ["path_1"],
    ">1.5.0": ["path_2"]
}
```
Then for version 2.0.0, the restriction will be `["path_2"]`.

#### Handling Unrecognized Versions

When a version is not recognized during comparison with a rule, the restriction applied will be that of the `*` operator. For example, if the configuration is:

```json
{
    "*": ["path_3"]
}
```

Then for all versions that fail to be parsed in SemVer format, the * restriction will be applied. For example, a version name like version_one will have the * restriction applied, resulting in ["path_3"].

Note that it is recommended to always include a rule for the `*` operator to cover any unrecognized versions.
 
