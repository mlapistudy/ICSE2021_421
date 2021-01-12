import io
import os
import sys
import datetime
import multiprocessing
import subprocess
import traceback
import time
import signal

import jedi


if sys.getdefaultencoding() != 'utf-8':
  reload(sys)
  sys.setdefaultencoding('utf-8')

class TimeoutException(Exception):   # Custom exception class
    pass

def timeout_handler(signum, frame):   # Custom signal handler
    raise TimeoutException

# Change the behavior of SIGALRM
signal.signal(signal.SIGALRM, timeout_handler)


class Repository(object):
  def __init__(self, name):
    self.name = name
    self.files = []

  def add_file(self, file_url):
    if len(file_url)>0:
      self.files.append(self.url_to_path(file_url))

  def url_to_path(self, file_url):
    file_name = file_url[(file_url.rindex("/")+1):]
    subdir = self.name.replace('/', '-')  
    return os.path.join(CODE_DIR, subdir, file_name)

  def get_subdir(self):
    subdir = self.name.replace('/', '-')  
    return os.path.join(CODE_DIR, subdir)

  def get_folder_files(self):
    subdir = self.name.replace('/', '-')  
    subdir = os.path.join(CODE_DIR, subdir)
    tmp_files = os.listdir(subdir)
    code_files = []
    for i in range(len(tmp_files)):
      file = os.path.join(subdir,tmp_files[i])
      # skip out some lib functions
      if ("/--float--" in file) or ("/--int--" in file) or ("/--str--" in file):
        continue
      code_files.append(file)
    return code_files

  def print_details(self):
    print(self.name)
    print(str(self.files))


def run_command(command):
  proc = subprocess.Popen(command, shell=True)
  proc.wait()

def read_wholefile(filename):
  with open(filename, 'r', encoding='utf8') as file_obj:
    text = file_obj.read()
  # replace("return","_____return_value=" ) to force jedi analyse return and print command
  return text

def read_repos():
  repo_list = []
  repo = None
  file = open(LIST_FILE, "r")
  for line in file.readlines(): 
    line = line.strip()
    if line.startswith("=="):
      if repo:
        repo_list.append(repo)
      repo = Repository(line.replace("=== ",""))
    else:
      repo.add_file(line)
  repo_list.append(repo)
  file.close()  
  # for repo in repo_list:
  #   repo.print_details()
  return repo_list


def search_score_mag(file_content, use_score, use_magnitude):
  # score_appear = search_row_col(content, '.score')
  # use_magnitude_appear = search_row_col(content, '.use_magnitude')
  # print(str((score_appear,use_magnitude_appear)))
  if file_content.find('.score') >=0:
    use_score = True
  if file_content.find('.magnitude') >=0:
    use_magnitude = True

  return use_score, use_magnitude


def analyze_repo(repo):
  global use_score
  global use_magnitude
  use_score = False
  use_magnitude = False

  code_files = repo.get_folder_files()
  for code_file in code_files:
    file_content = read_wholefile(code_file)
    use_score, use_magnitude = search_score_mag(file_content, use_score, use_magnitude)
    if use_score and use_magnitude:
      return 2


  if use_score and use_magnitude:
    return 2
  elif use_score or use_magnitude:
    return 1
  else:
    return 0




def main():
  repo_list = read_repos()
  answer = read_wholefile(INPUT_FILE).split("\n")

  file = open(RESULT_FILE, "w")

  for i in range(len(repo_list)):
    repo = repo_list[i]
    
    result = int(answer[i].split("\t")[1])

    if result < 0:
      result = analyze_repo(repo)

    print(repo.name+'\t'+str(result))
    # time.sleep(1)
    file.write(repo.name+'\t'+str(result)+'\n')
  file.close()



if __name__ == '__main__':
  API_NAME = "analyze_sentiment"
  CODE_DIR = "codes_final"
  LIST_FILE = "python_apps.txt"
  INPUT_FILE = "analyze_result.txt"
  RESULT_FILE = "fixed.txt"
  main()


