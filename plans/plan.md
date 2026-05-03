# instructions

- each step is it's own python feature
- these steps are designed to be distinct
- if a step does not have a file that is saved, this is a design error

# orchaestration root
- after each step, save the output of these functions to a file. 
- unlesss otherwise stated, all files should be replaced upon writing
- if we can find no more results on getting repos (step 1), a message is returned ot the user and we end
- if all repos from our candidate.json have been exausted in filter step (step 2), repeat to step 1 and grab another X amount of repos


# variables

X - number of repos to grab
Y - offest to continue searching

# definitions

## bom managed dependency override

The qualifying rule for a BOM-managed dependency override is: a project locally declares a dependency version even though an imported BOM already manages that same `groupId:artifactId`. External BOM artifacts should be resolved by downloading their POMs from Maven repositories and storing them in a folder relative to the project root as a cache.

## github issue ticket template

AI: create this

# step 1 - get repos

output_files: [candidates.json, repo_pom_xml...]

Build a one-shot Python CLI that queries GitHub for candidate Java repositories, filters to repos updated within the last 7 days and with at least 100 stars, with Maven `pom.xml` files that use parent BOMs. these repositories pom.xml files will be saved to the repos folder in the output_files entries. we can return X amount of repos each time, with an y amount of offset so that we can continue to search after additional filtering is completed later on.


# step 2 - filter repos

input_files: [processed.json, candidate.json]
output_files: [new_overrides.json]

remove all repos that
- allready exist in the output_files entry. 
- do not have a BOM-managed dependency override

put the resultant repos in the output_files entry


# step 3 - create github issue

input_files: [new_overrides.json]
output_files: [new_github_issues.json]

follow the github ticket template and create the title and description for a github issue. 

# step 4 - send github issues

input_files: new_github_issues.json
output_files: [processed.json]

output_schema_example: {"date_of_processing": {
        issues: [{ repo_url: string, link: string }]
}
}

create github issues based on the new input issues. the output_files entry should contain links to the issue that was created. this output_files entry should be appended, not replaced
