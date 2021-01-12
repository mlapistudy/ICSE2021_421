# README

This folder includes Output Mis-interpretation Checker.

## Files

`codes_subset` folder and `test.txt` includes some test data.

`codes` folder includes all related code files. It will be generated during the execution.

`python_apps.txt` and `repo_list_language.txt` are the repo list used in this checker. `repo_list_language.txt` are all Github applications using google language API. `python_apps.txt` is generated during execution, which contains python applications using `analyze_sentiment` API.

`analyze_result.txt` is the final result. It will be generated after the execution. The format is `[USERNAME/REPO] \t [# of fields used]`. An repo is regarded as correct only when the second column equals to 2.


## Credential

Github requires login to do search.

Please change line `client = Octokit::Client.new(:access_token => "your-token")` to your [OAuth access tokens](http://developer.github.com/v3/oauth/) in all ruby files (`search_repo.rb ` and `search_inside_repo.rb`). 

## Package dependency

Ruby 2.4 or higher. octokit package 4.18.0 or higher.

Python 3.6 or higher. jedi package 0.17.0 or higher.

## Execution

1. `ruby search_repo.rb` to get repo list and download related files. Its input is `repo_list_language.txt` and output is `python_apps.txt`, which are included in the folder
2. `python check_usage_pre.py` to download extra files for next step. The code are stored in `codes` file. Variable `TIME_LIMIT` sets time limit for each repo (0 for no limit).
3. `python check_usage.py` to do further checking. Variable `TIME_LIMIT` sets time limit for each repo. negative number refers to timeout or other failure. Variable `TIME_LIMIT` sets time limit for each repo.