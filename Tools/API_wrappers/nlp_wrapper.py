import io
import os
import sys
import re
from google.cloud import language_v1
from google.cloud.language_v1 import enums
import multiprocessing
import concurrent.futures

CHARGE_UNIT = 1000

def multi_threads_handler(func, inputs, thread_num):
  
  with concurrent.futures.ThreadPoolExecutor(max_workers=thread_num) as executor:
      outputs = executor.map(func, inputs)
  
  # Returns an iterable object of class 'generator'
  return outputs
  

# split text in to several pieces
def _split_text_by_sentence(text_content, list_num):
  text_list = []
  target_length = len(text_content) // list_num
  
  cur_string = ""
  sentences = re.split(r"([.。!！?？；;])", text_content)
  i = 0
  while i < len(sentences):
    if i+1 < len(sentences):
      sentence = sentences[i]+sentences[i+1] # add back punctuation
      i = i+1
    # print("<<<"+sentence)
    # 0.25 is for tuning
    if ((len(cur_string) + 0.25*len(sentence) >= target_length) or len(cur_string) + len(sentence) > CHARGE_UNIT) and not len(cur_string)==0:
      text_list.append(cur_string)
      cur_string = ""
    cur_string = cur_string + sentence
    i = i+1
  if len(cur_string)>=1:
    if len(text_list)<list_num:
      text_list.append(cur_string)
    else:
      text_list[-1] = text_list[-1] + cur_string

  # for text in text_list:
  #   print(">>>"+text)
  return text_list



# one string, one thread
def detect_entity_single_input_single_thread(text_content):
  text_content = text_content.strip()
  text_length = len(text_content)

  # out of limit
  if text_length > 1000000:
    detect_entity_single_input(text_content)

  try:
    client = language_v1.LanguageServiceClient()

    type_ = enums.Document.Type.PLAIN_TEXT
    language = "en"
    document = {"content": text_content, "type": type_, "language": language}
    encoding_type = enums.EncodingType.UTF8

    response = client.analyze_entities(document, encoding_type=encoding_type)

    entity_list = []

    for entity in response.entities:
      # put salience as list for multiple thread case
      entity_list.append({"name":entity.name, "salience":[entity.salience],
                          "metadata":entity.metadata, 
                          "mentions":list(entity.mentions)})
  except Exception as e: 
    print(e)
    return []

  return entity_list

def _merge_answers(answers, text_list):
  entity_list = []
  ans_num = -1
  for answer in answers:
    
    # increase mention offset to fix chunking
    ans_num += 1
    offset_fix = len(''.join(text_list[:ans_num]))

    for entity in answer:
      for j in range(len(entity["mentions"])):
        entity["mentions"][j].text.begin_offset += offset_fix

      flag = True
      for i in range(len(entity_list)):
        # if already exists
        if entity_list[i]["name"] == entity["name"]:
          flag = False
          # no need to process name and metadata
          entity_list[i]["salience"] = entity_list[i]["salience"] + entity["salience"]
          entity_list[i]["mentions"] = entity_list[i]["mentions"] + entity["mentions"]
          break
      if flag:
        entity_list.append(entity)
  return entity_list


# wrapper function for one string
# the max_thread setting depends on the maximum parallel API supported by service provider (Google)
# max_thread should be a positive integer
def detect_entity_single_input(text_content, max_thread=15):
  
  try:

    text_content = text_content.strip()
    text_length = len(text_content)

    # price unit is 1000 characters
    if text_length<=CHARGE_UNIT:
      return detect_entity_single_input_single_thread(text_content)

    if max_thread * CHARGE_UNIT > text_length:
      thread_num = int(text_length / CHARGE_UNIT) + 1
    else:
      thread_num = max_thread

    text_list = _split_text_by_sentence(text_content, thread_num)
    answers = multi_threads_handler(detect_entity_single_input_single_thread, text_list, thread_num)

    entity_list = _merge_answers(answers, text_list)


  except Exception as e: 
    print(e)
    return []

  return entity_list



# wrapper function for multiple string
# the max_thread setting depends on the maximum parallel API supported by service provider (Google)
# max_thread should be a positive integer
def detect_entity_batch(text_list, max_thread=15):

  def find_max_smaller_than(data_list, threshold):
    result = 0
    no = 0
    for i in range(len(data_list)):
      data = data_list[i]
      if data>result and data<=threshold:
        result = data
        no = i
    return no, result
  
  try:
    
    for i in range(len(text_list)):
      text_list[i] = text_list[i].strip()

    text_content = ' '.join(text_list)
    text_length = len(text_content)

    entity_list = detect_entity_single_input(text_content, max_thread)

    # result need to be break down
    final_entity_list = [] 
    for i in range(len(text_list)):
      final_entity_list.append([])

    # now fix offset and split answers
    to_minus = [0] * len(text_list)
    for i in range(1,len(text_list)):
      # +1 for ' ' in join
      to_minus[i] = to_minus[i-1] + len(text_list[i-1]) + 1

    

    for i in range(len(entity_list)):
      flag = [False] * len(text_list)
      for j in range(len(entity_list[i]["mentions"])):
        no, value = find_max_smaller_than(to_minus, entity_list[i]["mentions"][j].text.begin_offset)
        entity_list[i]["mentions"][j].text.begin_offset -= value
        flag[no] = True
      for j in range(len(text_list)):
        # to-do: remove unwanted mentions
        if flag[j]:
          final_entity_list[j].append(entity_list[i])

  except Exception as e: 
    print(e)
    return []

  return final_entity_list



if __name__ == '__main__':
  os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='your-credential.json'
  
  input_text_list = ["The story revolves around a girl.",
                "She is named after her red hooded.",
                "The girl walks through the woods.",
                "A Big Bad Wolf wants to eat the girl."]

  input_text_long = "The story revolves around a girl called Little Red Riding Hood. In Perrault's versions of the tale, she is named after her red hooded cape/cloak that she wears. The girl walks through the woods to deliver food to her sickly grandmother (wine and cake depending on the translation). In Grimms' version, her mother had ordered her to stay strictly on the path. A Big Bad Wolf wants to eat the girl and the food in the basket. He secretly stalks her behind trees, bushes, shrubs, and patches of little and tall grass. He approaches Little Red Riding Hood, who naively tells him where she is going. He suggests that the girl pick some flowers as a present for her grandmother, which she does. In the meantime, he goes to the grandmother's house and gains entry by pretending to be her. He swallows the grandmother whole (in some stories, he locks her in the closet) and waits for the girl, disguised as the grandma. When the girl arrives, she notices that her grandmother looks very strange. Little Red then says, \"What a deep voice you have!\" (\"The better to greet you with\", responds the wolf), \"Goodness, what big eyes you have!\" (\"The better to see you with\", responds the wolf), \"And what big hands you have!\" (\"The better to embrace you with\", responds the wolf), and lastly, \"What a big mouth you have\" (\"The better to eat you with!\", responds the wolf), at which point the wolf jumps out of the bed and eats her, too. Then he falls asleep. In Charles Perrault's version of the story (the first version to be published), the tale ends here. However, in later versions, the story continues generally as follows."

  # single input example
  response = detect_entity_single_input(input_text_long)
  print(str(response))

  # multiple input example
  responses = detect_entity_batch(input_text_list)
  for response in responses:
    print("==================================")
    print(str(response))





