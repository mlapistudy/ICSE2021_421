# INSTALL

The instructions are provided for Ubuntu System. For Mac OS, please use `brew` instead of `apt`.

## Python packages

### Install Python and pip

Our tools/checkers are mainly implemented in Python3.8. It can be installed with

```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.8
```

and verfied with

```bash
python3.8 --version
```

Then install package management tool pip with

```bash
sudo apt install python3-pip
```

and verfied with

```bash
pip3 --version
```

or 

```bash
/usr/bin/python3.8 -m pip --version
```

### Install Google Cloud AI

`Tools/API_wrappers` folder includes wrapper functions for Google Cloud AI Services.

To install these packages:

```bash
/usr/bin/python3.8 -m pip install google-cloud-language==1.3.0 --user
/usr/bin/python3.8 -m pip install google-cloud-vision==1.0.0 --user
/usr/bin/python3.8 -m pip install google-cloud-speech==2.0.0 --user
/usr/bin/python3.8 -m pip install google-cloud-texttospeech==2.2.0 --user
/usr/bin/python3.8 -m pip install google-api-python-client==1.10.0 --user
/usr/bin/python3.8 -m pip install google-auth-httplib2==0.0.4 --user
/usr/bin/python3.8 -m pip install google-auth-oauthlib --user
```

To enable APIs in Google account and create credentials, please following Google official document

1. Vision: https://cloud.google.com/vision/docs/setup
2. Speech-to-Text: https://cloud.google.com/speech-to-text/docs/quickstart-client-libraries
3. Language: https://cloud.google.com/natural-language/docs/setup

Then for files in  `Tools/API_wrappers` folder , please change line `os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='your-credential.json'` to the path of your certification.

### Install other packages

For other packages:

```bash
/usr/bin/python3.8 -m pip install pillow==5.3.0
/usr/bin/python3.8 -m pip install jedi==0.17.0
/usr/bin/python3.8 -m pip install astor==0.8.1
/usr/bin/python3.8 -m pip install anytree==2.8.0
/usr/bin/python3.8 -m pip install PyGithub==1.51
/usr/bin/python3.8 -m pip install urllib3==1.25.9
```



## Ruby packages

The output mis-interpretation checker also use Ruby packages to access Github APIs.

To install Ruby and gem:

```bash
sudo apt update
sudo apt install ruby-full
```

To verfiy Ruby:

```bash
ruby –v
```

To install packages to access Github APIs:

```bash
gem install octokit
```

Then for ruby files (`search_repo.rb ` and `search_inside_repo.rb`) in  `Tools/Output_Mis-interpretation_Checker` folder, please change line `client = Octokit::Client.new(:access_token => "your-token")` to your [OAuth access tokens](http://developer.github.com/v3/oauth/). 



## How to run tools

The code and data for tools are in `Tools` folder. Please follow the `readme.md` files in the subfolder.
