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
    "[]1.0.0, 3.0.0": [
        "path/to/folder3"
        ],
    "*": ["path/to/folder4"]
}
```

The operators that can be used in the configuration are ==, !=, <=, >=, <, >, [], ][, ]], [[ and *. The * operator means all versions without restriction. It is important to note that all rules are inclusive, meaning that if two or more rules match the same version, the combination of these rules will be used to include or exclude the folders.

In the example above, the first entry specifies that for versions less than or equal to 1.0.0, the folders "path/to/folder1" should be included or excluded except for the version 1.0.0, the folder "path/to/folder1" and "path/to/folder2" should be included or excluded. The second entry specifies that for versions greater than or equal to 1.0.0 but also lower than 3.0.0 included, the folder "path/to/folder3" should be included or excluded. The third entry specifies that for all other versions, the folder "path/to/folder4" should be included or excluded.

#### The `==` Operator

The `==` operator can be used to add exceptions to a rule. For example, if the configuration is:

```json
{
    "==1.5.0": ["path_1"],
    "1.5.0": ["path_1"]
}
```

Then for all versions greater than or equal to 1.0.0, the restriction will be `["path_1"]`. In addition, if a version is specified without an operator, the default operator used is `==`.

#### The `!=` Operator

The `!=` operator is the exact opposite of the `==` operator. For example, if the configuration is:

```json
{
    "!=1.5.0": ["path_1"]
}
```

Then for all versions except the version 1.5.0, will have the restriction `["path_1"]`.

#### The `<=` Operator

The `<`= operator is used to specify a maximum version restriction. For example, if the configuration is:

```json
{
    "<=2.0.0": ["path_1"]
}
```

Then for all versions less than or equal to 2.0.0 (inclusive), the restriction will be ["path_1"].


#### The `>=` Operator

The `>=` operator is used to specify a minimum version restriction. For example, if the configuration is:

```json
{
    ">=2.0.0": ["path_1"]
}
```

Then for all versions greater than or equal to 2.0.0 (inclusive), the restriction will be `["path_1"]`.

#### The `<` Operator

The `<` operator is used to specify a maximum version restriction, excluding the specified version. For example, if the configuration is:

```json
{
    "<2.0.0": ["path_1"]
}
```

Then for all versions less than 2.0.0 (exclusive), the restriction will be `["path_1"]`.

#### The `>` Operator

The `>` operator is used to specify a minimum version restriction, excluding the specified version. For example, if the configuration is:

```json
{
    ">2.0.0": ["path_1"]
}
```

Then for all versions greater than 2.0.0 (exclusive), the restriction will be ["path_1"].

#### The `]]` Operator

The `]]` operator is used to specify a range of versions, excluding both endpoints. For example, if the configuration is:

```json
{
    "]]1.0.0,2.0.0": ["path_1"]
}

```

Then for all versions greater than 1.0.0 (exclusive) and less than 2.0.0 (inclusive), the restriction will be ["path_1"].

#### The `[[` Operator

The `[[` operator is used to specify a range of versions, excluding both endpoints. For example, if the configuration is:

```json
{
    "[[1.0.0,2.0.0": ["path_1"]
}

```

Then for all versions greater than 1.0.0 (inclusive) and less than 2.0.0 (exclusive), the restriction will be ["path_1"].

#### The `[]` Operator

The `[]` operator is used to specify a range of versions, excluding both endpoints. For example, if the configuration is:

```json
{
    "[]1.0.0,2.0.0": ["path_1"],
    "1.0.0,2.0.0": ["path_1"],
}

```

Then for all versions greater than 1.0.0 (inclusive) and less than 2.0.0 (inclusive), the restriction will be ["path_1"]. In addition, two versions is specified without an operator, the default operator used is `[]`.

#### The `][` Operator

The `][` operator is used to specify a range of versions, excluding both endpoints. For example, if the configuration is:

```json
{
    "][1.0.0,2.0.0": ["path_1"]
}

```

Then for all versions greater than 1.0.0 (exclusive) and less than 2.0.0 (exclusive), the restriction will be ["path_1"].

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

#### Handling Unrecognized Versions

When a version is not recognized during comparison with a rule, the restriction applied will be that of the `*` operator. For example, if the configuration is:

```json
{
    "*": ["path_3"]
}
```

Then for all versions that fail to be parsed in SemVer format, the * restriction will be applied. For example, a version name like `invalid` will have the `*` restriction applied, resulting in `["path_3"]`.

Note that it is recommended to always include a rule for the `*` operator to cover any unrecognized versions. Additionally, the program will always attempt to construct a SemVer object from the version information found in the configuration, even if it is not in a valid SemVer format.

#### Resolving Conflicts in Rules

In case of conflicts in rules, the operator used in the rule defines the type of rule to be applied. For instance, if the configuration is:

```json
{
    "<=2.0.0,1.0.0": ["path_2"]
}
```

Then the rule will be interpreted as the same as:

```json
{
    "<=2.0.0": ["path_2"]
}
```

If a rule cannot be interpreted, it will be ignored by the program. For example, if the configuration is:

```json
{
    "[]1.0.0": ["path_2"]
}
```

Then the rule will be ignored by the program.
