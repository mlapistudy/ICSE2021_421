# README

This folder includes wrapper functions for Google Cloud AI Services. These wrappers are implemented in Python3.



## Files

`data` folder includes some test data.

`vision_wrapper.py` is for all Vision APIs.

`speech_to_text_wrapper.py` is for speech recognition.

`nlp_wrapper.py` is for entity detection.

`nlp_wrapper2.py` is for syntax analysis.

 The test examples are at the end of each file. Please check the comments for more details.


## Requirement

Python>=3.6

google-cloud-language==1.3.0

google-cloud-vision==1.0.0

google-cloud-speech==2.0.0

google-cloud-texttospeech==2.2.0


## Credential

Google Cloud AI Services require some set up before using, including installing libs, enabling APIs in Google account and creating credentials. Following are the Google official document for setting up:

1. Vision: https://cloud.google.com/vision/docs/setup
2. Speech-to-Text: https://cloud.google.com/speech-to-text/docs/quickstart-client-libraries
3. Language: https://cloud.google.com/natural-language/docs/setup
4. Text-to-Speech: https://cloud.google.com/text-to-speech/docs/quickstart-client-libraries

Please change line `os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='your-credential.json'` to the path of your certification.