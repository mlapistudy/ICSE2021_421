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
  with open(filename, 'r') as file_obj:
    text = file_obj.read()
  # modify a little bit to force jedi analyse this line
  return text.replace("return","_____return_value=").replace("print","_____return_value=")

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
  return repo_list

def search_row_col(file_content, substring):
  exists = []
  lineCount = 0
  for line in file_content.split('\n'):
    lineCount += 1
    if line.strip().startswith('#'):
      continue
    col = line.find(substring)
    if col >= 0:
      exists.append([lineCount, col, line])
  return exists

def search_score_mag(file_content, use_score, use_magnitude):
  if file_content.find('.score') >=0:
    use_score = True
  if file_content.find('.magnitude') >=0:
    use_magnitude = True
  return use_score, use_magnitude


def is_appear(content, variable):
  all_names = jedi.names(content, all_scopes=True, definitions=True, references=True)
  for name in all_names:
    if not name.full_name:
      continue
    if len(name.full_name) <=0:
      continue
    if name.full_name.endswith("."+variable):
      return True
  return False

# it will quit early
def search_references(script, content, name_string):
  global use_score
  global use_magnitude
  result = []
  to_search = []
  # replace("return","_____return_value=" ) to force jedi analyse return and print command
  # also use += to replace append
  content = content.replace("return", "_____return_value=").replace("print", "_____print=").replace(".append", "+=")
  all_names = jedi.names(content, 
    all_scopes=True, definitions=True, references=False)

  for name in all_names:
    if not name.full_name:
      continue
    if len(name.full_name) <=0:
      continue
    if name_string in name.description:
      # reduce some false postives
      if is_appear(name.description, name_string):
        left_value = name.description.strip().split('=')[0].strip()
        if left_value == name_string:
          continue
        result.append(name)
        if not "_____return_value" == name.full_name:
          to_search.append(left_value)
        use_score, use_magnitude = search_score_mag(name.description, use_score, use_magnitude)
        # if find two variables, then quit
        if use_score and use_magnitude:
          return result
  
  while True:
    len1 = len(result)
    to_search_new = []

    for search_item in to_search:
      for name in all_names:
        if not name.full_name:
          continue
        if len(name.full_name) <=0:
          continue
        if search_item in name.description:
          if is_appear(name.description, search_item):
            left_value = name.description.strip().split('=')[0].strip()
            if left_value == search_item:
              continue
            result.append(name)
            to_search_new.append(left_value)
            use_score, use_magnitude = search_score_mag(name.description, use_score, use_magnitude)
            if use_score and use_magnitude:
              return result

    to_search = to_search_new
    if len1 == len(result):
      return result

  return result


def find_left_value(content_line_by_line, script, line_num):
  line = content_line_by_line[line_num-1]
  col_num = 1+ len(line) - len(line.lstrip())
  try:
    line_script = script.goto(line_num, col_num)[0]
    left_value = line_script.full_name.split('.')[-1]
  except:
    if line_num >= 1:
      return find_left_value(content_line_by_line, script, line_num-1)
    else:
      return None
  return left_value


def get_reference_by_pos(script,pos):
  try:
    result = script.get_references(pos[0],pos[1])[0]
  except:
    if pos[0] >= 1:
      pos[0] = pos[0] - 1
      return get_reference_by_pos(script,pos)
    else:
      return None

  return result


# return 2 for good, 1/0 for bad, -1 for strange case
def analyze_repo(repo):
  global use_score
  global use_magnitude
  use_score = False
  use_magnitude = False
  error_flag = False

  # for each file
  for filename in repo.files:
    content = read_wholefile(filename)
    # too large to process
    content_line_by_line = content.split("\n")
    if len(content_line_by_line) > 1000:
      return -2
    script = jedi.Script(content)
    positions = search_row_col(content, API_NAME)

    # for each API reference
    for pos in positions:
      result = get_reference_by_pos(script,pos)
      # jedi.api.classes.Name: full_name, description, line,column defined_names(), is_definition()
      if not result:
        continue
      if not result.full_name:
        continue

      names = result.full_name.split('.') # full_name sample: __main__.detect_sentiment.analyze_sentiment
      appear_in_function = names[-2] 
      
      # check dataflow -> going down
      left_value = find_left_value(content_line_by_line, script, pos[0])
      if left_value:
        result = search_references(script, content, left_value)
      else:
        # if jedi cannot find left value for return
        if content_line_by_line[pos[0]-1].strip().startswith("return"):
          use_score, use_magnitude = search_score_mag(content_line_by_line[pos[0]-1], use_score, use_magnitude)
        result = []
      # if find two variables, then quit
      if use_score and use_magnitude:
        return 2
      
      # check function names
      function_names = []
      # script = jedi.Script(content)
      for mention in result:
        line_content = mention.description
        all_names = jedi.names(line_content, all_scopes=True, definitions=True, references=True)
        for name in all_names:
          name2 = name.full_name.split('.')[-1]
          if ("="+name2+"(") in line_content.replace(" ",""):
            if not (name2=="str" or name2=="float" or name2=="int"):
              function_names.append(name2)

      # if it's not apeared in a function, then no need to search for its existance
      if '__main__' in appear_in_function:
        pass
      else:
        function_names.append(appear_in_function)

      # start downloading related files
      for function in function_names:
        if ("def "+function) in content and (appear_in_function != function):
          continue
        if (function == "main"):
          continue
        command = "ruby search_inside_repo.rb " + function + " " + repo.name + " " + CODE_DIR
        run_command(command)
        time.sleep(1)

  if use_score and use_magnitude:
    return 2
  elif use_score or use_magnitude:
    return 1
  else:
    return 0
  return -1


def main():
  repo_list = read_repos()

  for repo in repo_list:
    result = -1
    signal.setitimer(signal.ITIMER_REAL, TIME_LIMIT)
    try:
      result = analyze_repo(repo)
      signal.setitimer(signal.ITIMER_REAL, 0)
    except TimeoutException:
      print("TIME OUT")
      result = -1
    except:
      signal.setitimer(signal.ITIMER_REAL, 0)
      # return 2 for good, 1/0 for bad, -1 for strange case
      result = -1
      traceback.print_exc()
    finally:
      # Reset the alarm
      signal.setitimer(signal.ITIMER_REAL, 0)
    print(repo.name+'\t'+str(result))
    time.sleep(1)


if __name__ == '__main__':
  API_NAME = "analyze_sentiment"
  CODE_DIR = "codes"
  LIST_FILE = "python_apps.txt"
  # CODE_DIR = "codes_subset"
  # LIST_FILE = "test.txt"
  TIME_LIMIT = 120
  main()


