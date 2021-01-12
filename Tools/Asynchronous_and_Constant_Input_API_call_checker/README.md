# README

# Asynchronous API call checker

This folder contains source files for the asynchronous API call checker. Note that this README documents batch processing. 

## Package dependencies

Python >= 3.8.0
astor >= 0.8.1
anytree >= 2.8.0
PyGithub >= 1.51
urllib3 >= 1.25.9

Note that Python 3.8 is required because the AST tool this file uses works **only in Python 3.8 or higher versions**. In previous versions errors are expected in AST-related executions.

## Credential

Github requires login to do search.

Please change line 
```python
g1 = github.Github("your-token")
g2 = github.Github("your-token")
g3 = github.Github("your-token")
```

 to your [OAuth access tokens](http://developer.github.com/v3/oauth/) in file `utils/github_search.py`.

It's fine to use only one Github account by filling in same token, and increase the value of `SLEEP_TIME`, which indicates the seconds. 



## Usage

### AWS

The main file for checking misuse of asynchronous API in AWS services is `async_main_aws.py`. The keyword strings contained there correspond to AWS Transcribe (Speech-to-Text) service. For the other two services where this tool can be applied to, please replace the relevant codes (line 25 - 26) with the following:

If applied to AWS Transcribe (Speech-to-Text) service:

```
ASYNC_KEYWORD_LIST = ["get_transcription_job", "get_medical_transcription_job", "list_transcription_jobs", "list_medical_transcription_jobs"]
ASYNC_KEYWORD_LIST_EXIST = ["start_transcription_job" , "start_medical_transcription_job"]
```

If applied to AWS Comprehend (NLP) service:

```
ASYNC_KEYWORD_LIST = ["describe_entities_detection_job", "describe_dominant_language_detection_job", "describe_key_phrases_detection_job","describe_sentiment_detection_job"]
ASYNC_KEYWORD_LIST_EXIST = ["start_entities_detection_job", "start_dominant_language_detection_job", "start_key_phrases_detection_job", "start_sentiment_detection_job"]
```

If applied to AWS Polly (Text-to-Speech) service:

```
ASYNC_KEYWORD_LIST = ["get_speech_synthesis_task"]
ASYNC_KEYWORD_LIST_EXIST = ["start_speech_synthesis_task"]
```

After respective modification, please run:

```
python async_main_aws.py [input_file] [output_file]
```

### Google Cloud

The main file for checking misuse of asynchronous API in Google Cloud services is `async_main_google.py`. There is nothing to modify for this file, which can only be applied to Google Cloud Speech-to-Text service. To use it, run the following:

```
python async_main_google.py [input_file] [output_file]
```

### Input file

In the usage codes above, `[input_file]` is a list of Github repos using the corresponding Google Cloud / AWS service. It needs to be in the following format:
``repo_name \t url``
on each line. There are existing repo list in such format in folder `repo_list`:

- `speechclient_res_Python.txt`, Google Cloud Speech-to-Text service repo list, input for `async_main_google.py`
- `transcribe_res_python.txt`, AWS Transcribe (Speech-to-Text) service repo list, input for `async_main_aws.py`
- `polly_res_python.txt`, AWS Polly (Text-to-Speech) service repo list, input for `async_main_aws.py`
- `comprehend_res_python.txt`, AWS Comprehend (NLP) service repo list, input for `async_main_aws.py`

### Output file

After `async_main_google.py` or `async_main_aws.py` finishes, please feed the output file above to `async_parse_outfile_google.py` or `async_parse_outfile_aws.py`, respectively, using:

```
python async_parse_outfile_google.py [output_file] [final_repo_list]
```

Or:

```
python async_parse_outfile_aws.py [output_file] [final_repo_list]
```

In this step, the files might interactively ask you if a praticular code snippet in between the async start statement and the while loop (or in Google's case, the result retrieving line) corresponds to any meaningful action. Please press `1`, when prompted, if you determine such code is doing meaningful job, or press `2` if you do not think so.

In this step, the files might interactively ask you to give feedback on whether a possibly-parallel case is truly a use of parallelism or not. In this case, information of the below form will appear:

```
***
Tree Number 1
('amazon_stt', 'SpeechToText.py', ['SpeechToText.py'])
***
Now searching to see if parallel API takes place in the same file as function traced
BOTH IDENTIFIED IN THE SAME FILE: [function: ('amazon_stt', 'https://raw.githubusercontent.com/xuezzou/conversation-interface/699702d724fc24950604fba360990cc8be894f00/SpeechToText.py', ['https://raw.githubusercontent.com/xuezzou/conversation-interface/699702d724fc24950604fba360990cc8be894f00/SpeechToText.py'])] [url: https://raw.githubusercontent.com/xuezzou/conversation-interface/699702d724fc24950604fba360990cc8be894f00/SpeechToText.py
```

The parts within `***` are the function call tree. Each node is a 3-tuple. The first element is the function's call name, the second element is where this function is definied in, and the third element is the list of file(s) where this function appears in. You are seeing this print out for a particular project if and only if one of the function traced in the above function call tree also appears in the same file as a parallelism-related API/library. The overlap-related information is contained in the `BOTH IDENTIFIED IN THE SAME FILE` sentences.

After this file executes, a summary list will appear with how many projects fall in what category. The same list will also appear at the end of the user-specified `[final_repo_list]` file.

- `No use of Async` corresponds to cases where none of the keywords in `ASYNC_KEYWORD_LIST_EXIST` is found in the Github repository.
- `Github search exceptions` and `Processing exceptions` corresponds to cases where exceptions were generated.
- **(in AWS services only)** `Use of Lambda Function` corresponds to cases where the async APIs are called inside AWS Lambda services. In such cases, the exact parallelism-related workflow of an application is difficult to understand. *These cases should be treated as no misuse of async API by this auto-tool.*
- `No retrieve result` corresponds to cases where keyword(s) in `ASYNC_KEYWORD_LIST_EXIST` is(are) found but none of `ASYNC_KEYWORD_LIST` is found in the Github repository. Thus, such projects only submit jobs to AWS services but do not actually retrieve the results.
- `No pattern identified` corresponds to cases where we can not easily categorize them. *These cases should be treated as no misuse of async API by this auto-tool.*
- `No use of parallelism` corresponds to a misuse case of async API
- `Possible use of parallel cases` are cases where the file prompts users to give feedback based on the function call tree. *If no manual intervention were given, such cases should be treated as no misuse of async API by this auto-tool.* In the `After MANUAL INSPECTION:` section, these are split either towards `No use of parallelism` or `Use of parallel cases`
- `Codes in between (not counted towards the final count below)` corresponds to time when file prompts user to give feedback based on code snippet. This is for reference only.

## Computing number of projects with async misuse

### Before manual inspection

Looking at the numbers before manual inspection, please negelect the `No use of Async`, `Github search exceptions`, `No retrieve result`, and `Processing exceptions` numbers. Please count `Use of Lambda Function`, `Possible use of parallel cases`, and `No pattern identified` cases towards **no misuse**. Count `No use of parallelism` cases towards *misuse*.

### After manual inspection

Looking at the numbers after manual inspection, please negelect the `No use of Async`, `Github search exceptions`, `No retrieve result`, and `Processing exceptions` numbers. Please count `Use of Lambda Function`, `Use of parallel cases`, and `No pattern identified` cases towards **no misuse**. Count `No use of parallelism` cases towards *misuse*.





# Constant Input checker

This folder contains source files for the asynchronous API call checker.

## Package dependencies

Python >= 3.8.0
anytree >= 2.8.0
PyGithub >= 1.51
urllib3 >= 1.25.9

Note that Python 3.8 is required because that the AST tool this file uses works **only in Python 3.8 or higher versions**. In previous versions errors are expected in AST-related executions.



## Credential

Github requires login to do search.

Please change line 

```python
g1 = github.Github("your-token")
g2 = github.Github("your-token")
g3 = github.Github("your-token")
```

 to your [OAuth access tokens](http://developer.github.com/v3/oauth/) in file `utils/github_search.py`.

It's fine to use only one Github account by filling in same token, and increase the value of `SLEEP_TIME`, which indicates the seconds. 



## Usage

```
constant_input_main_google.py [input_file] [output_file]
```

Or,

```
constant_input_main_aws.py [input_file] [output_file]
```

### Input file

In the usage codes above, `[input_file]` is a list of Github repos using the corresponding Google Cloud / AWS service. It needs to be in the following format:
``repo_name \t url`` 
on each line. There are existing repo list in such format in folder `repo_list`:

- `texttospeech_res_Python.txt`, Google Cloud Text-to-Speech service repo list, input for `constant_input_main_google.py`
- `polly_res_python.txt`, AWS Polly (Text-to-Speech) service repo list, input for `constant_input_main_aws.py`

### Output file

After `constant_input_main_google.py` or `constant_input_main_aws.py` finishes, please feed the output file above to `constant_input_parse_outfile.py` using:

```
python constant_input_parse_outfile [output_file] [final_repo_list]
```

In this step, the files might interactively prompt detected entirely constants input to the API. Please judge if you believe they correspond to (1) actual constant; (2) not a constant; (3) constant for unit tests. The final result will be printed out and stored in file `[final_repo_list]`.