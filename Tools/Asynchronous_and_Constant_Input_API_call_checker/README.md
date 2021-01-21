# Table of contents
1. [Asynchronous API call checker](#async_top)
    1. [Package dependencies](#async_pack)
    2. [Credentials](#async_credential)
    3. [Usage](＃async_usage)
        1. [AWS](#async_usage_aws)
        2. [Google Cloud](#async_usage_google)
        3. [Input File](#async_usage_input_file)
        4. [Output File](#async_usage_output_file)
2. [Constant Input checker](#constant_top)
    1. [Package dependencies](#constant_pack)
    2. [Credentials](#constant_credential)
    3. [Usage](＃constant_usage)
        1. [Input File](#constant_input_file)
        2. [Output File](#constant_output_file)
3. [Replicate results in paper](#replicate_top)   

# Asynchronous API call checker <a name="async_top"></a>

This folder contains source files for the asynchronous API call checker. Note that this README documents batch processing. 

## Package dependencies <a name="async_pack"></a>

Python >= 3.8.0
astor >= 0.8.1
anytree >= 2.8.0
PyGithub >= 1.51
urllib3 >= 1.25.9

Note that Python 3.8 is required because the AST tool this file uses works **only in Python 3.8 or higher versions**. In previous versions errors are expected in AST-related executions.

## Credential <a name="async_credential"></a>

Github requires login to do search.

Please change line 
```python
g1 = github.Github("your-token")
g2 = github.Github("your-token")
g3 = github.Github("your-token")
```

to your [OAuth access tokens](http://developer.github.com/v3/oauth/) in file `utils/github_search.py`.

Because this tool is designed to be used for batch processing, it makes use of multiple (3) github accounts interchangably to crawl information.
Thus, if any particular account exceeds the rate limit, it can switch to other ones to continue crawling.
This tool automatically sleeps when it catches that all 3 accounts all exceed the rate limit.
As such, it's fine to use only one Github account by filling in same token.

## Usage <a name="async_usage"></a>

### AWS <a name="async_usage_aws"></a>

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

### Google Cloud <a name="async_usage_google"></a>

The main file for checking misuse of asynchronous API in Google Cloud services is `async_main_google.py`. There is nothing to modify for this file, which can only be applied to Google Cloud Speech-to-Text service. To use it, run the following:

```
python async_main_google.py [input_file] [output_file]
```

### Input file <a name="async_usage_input_file"></a>

In the usage codes above, `[input_file]` is a list of Github repos using the corresponding Google Cloud / AWS service. It needs to be in the following format:
``repo_name \t url``
on each line. There are existing repo list in such format in folder `repo_list`:

- `speechclient_res_Python.txt`, Google Cloud Speech-to-Text service repo list, input for `async_main_google.py`
- `transcribe_res_python.txt`, AWS Transcribe (Speech-to-Text) service repo list, input for `async_main_aws.py`
- `polly_res_python.txt`, AWS Polly (Text-to-Speech) service repo list, input for `async_main_aws.py`
- `comprehend_res_python.txt`, AWS Comprehend (NLP) service repo list, input for `async_main_aws.py`

### Output file <a name="async_usage_output_file"></a>

After `async_main_google.py` or `async_main_aws.py` finishes, please feed the output file above to `async_parse_outfile_google.py` or `async_parse_outfile_aws.py`, respectively, using:

```
python [-FLAG] async_parse_outfile_google.py [output_file] [final_repo_list]
```

Or:

```
python [-FLAG] async_parse_outfile_aws.py [output_file] [final_repo_list]
```

where `[-FLAG]` is either `-m` for interactive manual inspection (see below) or `-a` for automated results. Manual inspection are needed to fine-tune the results of these tools. For which ones are used in our paper, see section [Replicate results in paper](#replicate_top).

#### Manual inspection: meaningful code lines between async start and async retrival

A project might choose to complete certain actions between (1) submission of job to async API and (2) retrieval of data from async API. Our tool handles some basic cases in which certain trivial actions are taken between those two lines. For the remaining ones, if you choose to manually check them:

The files will interactively ask you if a praticular code snippet in between the async start statement and the while loop (or in Google's case, the result retrieving line) corresponds to any meaningful action. Please press `1`, when prompted, if you determine such code is doing meaningful job, or press `2` if you do not think so.

```
Nodes in between start statement and while statement

if not operation.done():

    print('Waiting for results...')
```

#### Manual inspection: possibly parallel case


In this step, the files might interactively ask you to give feedback on whether a possibly-parallel case is truly a use of parallelism or not. In this case, information of the below form will appear:

```
***

Tree Number 1

('stt_from_uri', 'flask_app/STT_utils.py', ['flask_app/app.py', 'flask_app/STT_utils.py'])

+-- ('upload_file', 'flask_app/app.py', ['flask_app/app.py'])

***

Now searching to see if parallel API takes place in the same file as function traced

BOTH IDENTIFIED IN THE SAME FILE: [function: ('stt_from_uri', 'https://raw.githubusercontent.com/Boscillator/AForAccessibility/e4515359c34e3d65f2ae47c023ca6751d2b782f0/flask_app/STT_utils.py', ['https://raw.githubusercontent.com/Boscillator/AForAccessibility/e4515359c34e3d65f2ae47c023ca6751d2b782f0/flask_app/app.py', 'https://raw.githubusercontent.com/Boscillator/AForAccessibility/e4515359c34e3d65f2ae47c023ca6751d2b782f0/flask_app/STT_utils.py'])] [url: https://raw.githubusercontent.com/Boscillator/AForAccessibility/e4515359c34e3d65f2ae47c023ca6751d2b782f0/flask_app/app.py

BOTH IDENTIFIED IN THE SAME FILE: [function: ('upload_file', 'https://raw.githubusercontent.com/Boscillator/AForAccessibility/e4515359c34e3d65f2ae47c023ca6751d2b782f0/flask_app/app.py', ['https://raw.githubusercontent.com/Boscillator/AForAccessibility/e4515359c34e3d65f2ae47c023ca6751d2b782f0/flask_app/app.py'])] [url: https://raw.githubusercontent.com/Boscillator/AForAccessibility/e4515359c34e3d65f2ae47c023ca6751d2b782f0/flask_app/app.py
```

The parts within `***` are the function call tree. Each node is a 3-tuple. The first element is the function's call name, the second element is where this function is definied in, and the third element is the list of file(s) where this function appears in. You are seeing this print out for a particular project if and only if one of the function traced in the above function call tree also appears in the same file as a parallelism-related API/library. The overlap-related information is contained in the `BOTH IDENTIFIED IN THE SAME FILE` sentences.

In this particular case, one can see that `upload_file` is called with `process_pool.apply_async` in file https://raw.githubusercontent.com/Boscillator/AForAccessibility/e4515359c34e3d65f2ae47c023ca6751d2b782f0/flask_app/app.py, so it should be counted as a **use-parallelism** case.


After this file executes, a summary list will appear with how many projects fall in what category. The same list will also appear at the end of the user-specified `[final_repo_list]` file.

<!-- - `No use of Async` corresponds to cases where none of the keywords in `ASYNC_KEYWORD_LIST_EXIST` is found in the Github repository.
- `Github search exceptions` and `Processing exceptions` corresponds to cases where exceptions were generated.
- **(in AWS services only)** `Use of Lambda Function` corresponds to cases where the async APIs are called inside AWS Lambda services. In such cases, the exact parallelism-related workflow of an application is difficult to understand. *These cases should be treated as no misuse of async API by this auto-tool.*
- `No retrieve result` corresponds to cases where keyword(s) in `ASYNC_KEYWORD_LIST_EXIST` is(are) found but none of `ASYNC_KEYWORD_LIST` is found in the Github repository. Thus, such projects only submit jobs to AWS services but do not actually retrieve the results.
- `No pattern identified` corresponds to cases where we can not easily categorize them. *These cases should be treated as no misuse of async API by this auto-tool.*
- `No use of parallelism` corresponds to a misuse case of async API
- `Possible use of parallel cases` are cases where the file prompts users to give feedback based on the function call tree. *If no manual intervention were given, such cases should be treated as no misuse of async API by this auto-tool.* In the `After MANUAL INSPECTION:` section, these are split either towards `No use of parallelism` or `Use of parallel cases`
- `Codes in between (not counted towards the final count below)` corresponds to time when file prompts user to give feedback based on code snippet. This is for reference only. -->

<!-- ## Computing number of projects with async misuse

### Before manual inspection

Looking at the numbers before manual inspection, please negelect the `No use of Async`, `Github search exceptions`, `No retrieve result`, and `Processing exceptions` numbers. Please count `Use of Lambda Function`, `Possible use of parallel cases`, and `No pattern identified` cases towards **no misuse**. Count `No use of parallelism` cases towards *misuse*.

### After manual inspection

Looking at the numbers after manual inspection, please negelect the `No use of Async`, `Github search exceptions`, `No retrieve result`, and `Processing exceptions` numbers. Please count `Use of Lambda Function`, `Use of parallel cases`, and `No pattern identified` cases towards **no misuse**. Count `No use of parallelism` cases towards *misuse*.

 -->


# Constant Input checker <a name="constant_top"></a>

This folder contains source files for the asynchronous API call checker.

## Package dependencies <a name="constant_pack"></a>

Python >= 3.8.0
anytree >= 2.8.0
PyGithub >= 1.51
urllib3 >= 1.25.9

Note that Python 3.8 is required because that the AST tool this file uses works **only in Python 3.8 or higher versions**. In previous versions errors are expected in AST-related executions.


## Credential <a name="constant_credential"></a>

Github requires login to do search.

Please change line 

```python
g1 = github.Github("your-token")
g2 = github.Github("your-token")
g3 = github.Github("your-token")
```

to your [OAuth access tokens](http://developer.github.com/v3/oauth/) in file `utils/github_search.py`.

Because this tool is designed to be used for batch processing, it makes use of multiple (3) github accounts interchangably to crawl information.
Thus, if any particular account exceeds the rate limit, it can switch to other ones to continue crawling.
This tool automatically sleeps when it catches that all 3 accounts all exceed the rate limit.
As such, it's fine to use only one Github account by filling in same token.


## Usage <a name="constant_usage"></a>

```
constant_input_main_google.py [input_file] [output_file]
```

Or,

```
constant_input_main_aws.py [input_file] [output_file]
```

### Input file <a name="constant_input_file"></a>

In the usage codes above, `[input_file]` is a list of Github repos using the corresponding Google Cloud / AWS service. It needs to be in the following format:
``repo_name \t url`` 
on each line. There are existing repo list in such format in folder `repo_list`:

- `texttospeech_res_Python.txt`, Google Cloud Text-to-Speech service repo list, input for `constant_input_main_google.py`
- `polly_res_python.txt`, AWS Polly (Text-to-Speech) service repo list, input for `constant_input_main_aws.py`

### Output file <a name="constant_output_file"></a>

After `constant_input_main_google.py` or `constant_input_main_aws.py` finishes, please feed the output file above to `constant_input_parse_outfile.py` using:

```
python constant_input_parse_outfile [output_file] [final_repo_list]
```

In this step, the files might interactively prompt detected entirely constants input to the API. Please judge if you believe they correspond to (1) actual constant; (2) not a constant; (3) constant for unit tests. The final result will be printed out and stored in file `[final_repo_list]`.

# Replicate results in paper <a name="replicate_top"></a>

Our paper's results related to these tools, contained in **section VII**, were obtained using the crawled repo lists in Aug. 2020. The `async_main_aws.py`, `async_main_google.py`, `constant_input_main_aws.py`, and `constant_input_main_google.py` (referred to as the "static analyzers" in tables below) were ran in Aug. 2020. If one runs these static analyzers on the same repo list (first column in tables below) again in a later date, some minor discrepencies might be observed due to projects being taken down or modified. Thus, we include the final output of these analyers in folder `results` (second column in tables below). To replicate the results of paper, one can run just run the `parse_outfile` scripts to get from second column to third column, as documented in [async](#async_usage_output_file) and [constant](#constant_output_file) output file sections. The complete workflow of these tools should be:

**Async tools:**
| Input Repo List<br>(contained in `repo_list`) | Output of static analyzers<br>(contained in `results`) | Output of `async_parse_outfile_*.py` scripts<br>(contained in `results`)          |
|-----------------------------------------------|--------------------------------------------------------|------------------------------------------------------------------------|
| `speechclient_res_Python.txt`                 | `google_async_stt_list.txt`                            | `google_async_stt_list_auto.txt`<br>`google_async_stt_list_manual.txt` |
| `polly_res_python.txt`                        | `aws_async_tts_out.txt`                                | `aws_async_tts_list_auto.txt`<br>`aws_async_tts_list_manual.txt`       |
| `comprehend_res_python.txt`                   | `aws_async_nlp_out.txt`                                | `aws_async_nlp_list_auto.txt`<br>`aws_async_nlp_list_manual.txt`       |
| `transcribe_res_python.txt`                   | `aws_async_stt_out.txt`                                | `aws_async_stt_list_auto.txt`                                          |

The `*_auto.txt` files in the last column were ran with the `-a` flag turned on in `async_parse_outfile_*.py`, and the `*_manual.txt` files in the last column were ran with the `-m` flag turned on in `async_parse_outfile_*.py`

**Constant input tools:**
| Input Repo List<br>(contained in `repo_list`) | Output of static analyzers<br>(contained in `results`) | Output of `constant_input_parse_outfile.py` scripts<br>(contained in `results`) |
|-----------------------------------------------|--------------------------------------------------------|---------------------------------------------------------------|
| `texttospeech_res_Python.txt`                 | `google_constant_out.txt`                              | `google_constant_list.txt`                                    |
| `polly_res_Python.txt`                        | `aws_constant_out.txt`                                 | `aws_constant_list.txt`                                       |

The final counts from the last column of these two tables make up the data in **section VII** of our paper.