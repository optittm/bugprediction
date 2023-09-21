# Next Version Risk Assessment Method

This document presents a method specifically designed to assess risks associated with deploying the next version of software. This method utilizes weighted metrics collected from previous versions of the software to provide a quantitative assessment of potential risks.

## Overview

Assessing the risks of the next software version is a critical step in software project management. It enables development teams to make informed decisions about the opportune time to release a new version by identifying the risks in the version and proposing key performance indicators (KPIs) for these risks.

The implemented method is based on the principles of multi-criteria analysis, notably employing the TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) method. This approach allows for the comparison of versions based on multiple criteria and determining the impact value of different metrics.

## How It Works

The calculation of the risk score is accomplished using the TOPSIS algorithm. To achieve this, we have implemented both criteria and basic alternatives. The criteria include the number of bugs, while the alternatives encompass bug velocity, the number of changes, the average experience of the development team, cyclomatic complexity, churn rate, and the number of legacy files. The process of adding additional alternatives and criteria will be explained in another section of this document.

The underlying concept of this algorithm is to determine the weights for each of these alternatives to perform the risk score calculation. To determine these weights, we create a correlation matrix between the alternatives and criteria. However, it's possible that there may not be a linear correlation among them. Therefore, we need to determine this by testing different correlation methods and selecting the one with the highest correlation coefficient. We take the absolute values of this correlation matrix to adhere to the necessary monotonicity principle for the TOPSIS algorithm.

At this stage, we have two key hypotheses: strongly correlated values impact each other, and the alternatives impact the criteria. Using this decision matrix, we can execute the TOPSIS algorithm, which involves several steps.

1. **Normalization**: First, the data for each criterion and alternative are normalized. This step ensures that all criteria are on the same scale and avoids bias due to differences in measurement units.

2. **Weight Assignment**: As mentioned earlier, the correlation matrix helps determine the weights for each alternative with respect to the criteria. These weights reflect the relative importance of each criterion in the risk assessment process.

3. **Ideal and Anti-Ideal Solutions**: The ideal and anti-ideal solutions are calculated for each criterion. The ideal solution represents the best possible value for each criterion, while the anti-ideal solution represents the worst possible value. The ideal solution is calculated by taking the maximum value for benefit criteria and the minimum value for cost criteria, while the anti-ideal solution is the opposite.

4. **Similarity Scores**: For each alternative, TOPSIS calculates the similarity score (closeness) to the ideal solution and the anti-ideal solution for all criteria. This is done using distance metrics such as the Euclidean distance or Minkowski distance.

Once the algorithm completes, the normalized distances represent the impact of each alternative on all the criteria, effectively serving as the weightings for the risk score calculation. To calculate the risk score, we simply sum the products of the metrics with their corresponding weights.

## How to Use This Method

### Add New Criteria or Alternative

To extend the functionality of this risk assessment method by adding new criteria or alternatives, follow these steps:

#### Adding a New Criterion

1. In the project's root directory, navigate to the "utils" folder.

2. Inside the "utils" folder, you will find two Python files named "criterion.py" and "alternatives.py." These files are structured to allow easy extension of criteria and alternatives.

3. To add a new criterion, create a new Python class that inherits from the abstract class Criterion defined in "criterion.py." The class should implement the following methods:
    - `get_name()`: This method should return the name used to retrieve the criterion's values using the `get_data` method.
    - `get_direction()`: Return a constant that indicates whether the criterion should be maximized or minimized. You can use `mt.Math.TOPSIS.MAX` or `mt.Math.TOPSIS.MIN` from the provided mt module.

4. After implementing the new criterion class, add an instance of it to the `criteria_map` dictionary in the `CriterionParser` class within "criterion.py." This dictionary maps criterion names to their respective classes.

#### Adding a New Alternative

1. Similar to adding a new criterion, create a new Python class that inherits from the abstract class `Alternative` defined in "alternatives.py."

2. Implement the `get_name()` method in your new alternative class. This method should return the name used to identify the alternative.

3. After implementing the new alternative class, add an instance of it to the `alternatives_map` dictionary in the `AlternativesParser` class within "alternatives.py." This dictionary maps alternative names to their respective classes.

By following these steps, you can seamlessly expand the set of criteria and alternatives available for risk assessment within the method, enabling a more comprehensive evaluation of your software's next version.

### Example of Retrieving Criteria and Alternatives

To retrieve criteria and alternatives from environment variables defined in a .env file, follow this example code. This step is essential to prepare the data for use in the TOPSIS algorithm.

```python
# Prepare data for TOPSIS
criteria_parser = CriterionParser()
alternative_parser = AlternativesParser()

criteria_names = configuration.topsis_criteria
criteria_weights = configuration.topsis_weigths
alternative_names = configuration.topsis_alternatives

try:
    criteria = criteria_parser.parse_criteria(criteria_names, criteria_weights)
except (InvalidCriterionError, MissingWeightError, NoCriteriaProvidedError) as e:
    print(f"Error: {e}")
    return

try:
    alternatives = alternative_parser.parse_alternatives(alternative_names)
except (InvalidAlternativeError, NoAlternativeProvidedError) as e:
    print(f"Error: {e}")
    return
```

#### Code Explanation

1. We use the `CriterionParser` and `AlternativesParser` classes to parse and convert the names of criteria and alternatives from environment variables defined in a `.env` file.

2. Criterion names are extracted from `configuration.topsis_criteria`, criterion weights from `configuration.topsis_weights`, and alternative names from `configuration.topsis_alternatives`. These values are typically stored in a configuration file or a `.env` file for more flexible management.

3. We use `try` and `except` blocks to handle potential errors related to retrieving criteria and alternatives. These errors include `InvalidCriterionError`, `MissingWeightError`, `NoCriteriaProvidedError`, `InvalidAlternativeError`, and `NoAlternativeProvidedError`.

Once this code is successfully executed, you have retrieved the necessary criteria and alternatives from your environment variables. You can then use the `get_data` method of the criteria and alternatives to obtain the corresponding data from your dataset, thus preparing the essential information for the TOPSIS algorithm.

### Example of Decision Matrix Construction

Constructing the decision matrix is a crucial step in the TOPSIS-based risk assessment method. This matrix serves as the foundation for evaluating the alternatives against the defined criteria. Here's an example code illustrating the process:

```python
# Create the decision matrix
decision_matrix_builder = mt.Math.DecisionMatrixBuilder()

# Add criteria to the decision matrix
for criterion in criteria:
    decision_matrix_builder.add_criteria(criterion.get_data(df), criterion.get_name())

# Add alternatives to the decision matrix
for alternative in alternatives:
    decision_matrix_builder.add_alternative(alternative.get_data(df), alternative.get_name())

# Set correlation methods if provided in the configuration
methods = []
for method in configuration.topsis_corr_method:
    methods.append(mt.Math.get_correlation_methods_from_name(method))
if len(methods) > 0:
    decision_matrix_builder.set_correlation_methods(methods)

# Build the decision matrix
decision_matrix = decision_matrix_builder.build()
```

#### Code Explanation

1. We begin by creating an instance of the `DecisionMatrixBuilder` from the `mt.Math` module. This builder will help us construct the decision matrix.

2. Next, we iterate through the criteria selected earlier, which were parsed and retrieved from environment variables. For each criterion, we call `criterion.get_data(df)` to obtain the normalized data from the DataFrame `df`, and `criterion.get_name()` to get the criterion's name. We then add this data and name to the decision matrix builder using `decision_matrix_builder.add_criteria()`.

3. Similarly, we iterate through the alternatives and add their normalized data and names to the decision matrix builder using `decision_matrix_builder.add_alternative()`.

4. If correlation methods have been provided in the configuration, we set these methods using `decision_matrix_builder.set_correlation_methods()`. This step is crucial for determining the relationships between the criteria and alternatives.

5. Finally, we build the decision matrix by calling `decision_matrix_builder.build()`. This results in a fully constructed decision matrix that includes all the selected criteria and alternatives, allowing us to proceed with the TOPSIS algorithm for risk assessment.

By following this code example, you'll have successfully created the decision matrix required for the subsequent steps in the risk assessment process using TOPSIS.

### Example of Using the Decision Matrix in TOPSIS

Once the decision matrix has been constructed, you can proceed to perform the TOPSIS analysis. Here's an example code illustrating how to use the decision matrix in the TOPSIS algorithm:

```python
# Compute TOPSIS
ts = mt.Math.TOPSIS(
    decision_matrix,
    [criterion.get_weight() for criterion in criteria], 
    [criterion.get_direction() for criterion in criteria]
)
ts.topsis()
```

#### Code Explanation

1. We create an instance of the `mt.Math.TOPSIS` class, which is responsible for performing the TOPSIS analysis. We pass three essential parameters to initialize it:
    - `decision_matrix`: This is the decision matrix constructed earlier, containing all the criteria and alternatives.
    - `[criterion.get_weight() for criterion in criteria]`: Here, we provide a list of weights for each criterion. These weights reflect the relative importance of each criterion in the risk assessment process. We retrieve these weights from the `criteria` list, which contains the parsed criteria objects.
    - `[criterion.get_direction() for criterion in criteria]`: This list specifies whether each criterion should be maximized or minimized. We retrieve this information from the criteria list as well.

2. After initializing the TOPSIS class, we call the `ts.topsis()` method to execute the TOPSIS algorithm. This method will perform all the necessary calculations and store the results for further analysis.

Once the TOPSIS analysis is completed, you can utilize the following methods available in the TOPSIS class:

- `get_closeness()`: This method returns an array of relative closeness values for each alternative. These values represent the degree of preference for each alternative based on the TOPSIS analysis.

- `get_ranking()`: It returns the ranking of alternatives based on their relative closeness values. The ranking is determined by sorting the relative closeness values in descending order and assigning ranks to the alternatives accordingly.

- `get_coef_from_label(label)`: This method allows you to retrieve the coefficient value associated with a specific alternative, given its label.

By using these methods, you can gain insights into the rankings and preferences of alternatives based on the TOPSIS analysis, helping you make informed decisions regarding the risk assessment for your software's next version.
