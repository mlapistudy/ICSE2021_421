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
def analyze_syntax_single_input_single_thread(text_content):
  text_content = text_content.strip()
  text_length = len(text_content)

  # out of limit
  if text_length > 1000000:
    analyze_syntax_single_input(text_content)

  try:
    client = language_v1.LanguageServiceClient()

    type_ = enums.Document.Type.PLAIN_TEXT
    language = "en"
    document = {"content": text_content, "type": type_, "language": language}
    encoding_type = enums.EncodingType.UTF8

    response = client.analyze_syntax(document, encoding_type=encoding_type)

    token_list = []

    for token in response.tokens:
      token_list.append({"text":token.text, "part_of_speech":token.part_of_speech,
                          "Lemma":token.lemma, "dependency_edge":token.dependency_edge})
  except Exception as e: 
    print(e)
    return []

  return token_list

def _merge_answers(answers, text_list):
  token_list = []
  ans_num = -1
  for answer in answers:
    
    # increase mention offset to fix chunking
    ans_num += 1
    offset_fix = len(''.join(text_list[:ans_num]))

    for token in answer:
      token["text"].begin_offset += offset_fix
      token_list.append(token)
  return token_list


# wrapper function for one string
# the max_thread setting depends on the maximum parallel API supported by service provider (Google)
# max_thread should be a positive integer
def analyze_syntax_single_input(text_content, max_thread=15):
  
  try:

    text_content = text_content.strip()
    text_length = len(text_content)

    # price unit is 1000 characters
    if text_length<=CHARGE_UNIT:
      return analyze_syntax_single_input_single_thread(text_content)

    if max_thread * CHARGE_UNIT > text_length:
      thread_num = int(text_length / CHARGE_UNIT) + 1
    else:
      thread_num = max_thread

    text_list = _split_text_by_sentence(text_content, thread_num)
    answers = multi_threads_handler(analyze_syntax_single_input_single_thread, text_list, thread_num)

    token_list = _merge_answers(answers, text_list)

  except Exception as e: 
    print(e)
    return []

  return token_list



# wrapper function for multiple string
# the max_thread setting depends on the maximum parallel API supported by service provider (Google)
# max_thread should be a positive integer
def analyze_syntax_batch(text_list, max_thread=15):

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

    token_list = analyze_syntax_single_input(text_content, max_thread)

    # result need to be break down
    final_token_list = [] 
    for i in range(len(text_list)):
      final_token_list.append([])

    # now fix offset and split answers
    to_minus = [0] * len(text_list)
    for i in range(1,len(text_list)):
      # +1 for ' ' in join
      to_minus[i] = to_minus[i-1] + len(text_list[i-1]) + 1

    for i in range(len(token_list)):
      no, value = find_max_smaller_than(to_minus, token_list[i]["text"].begin_offset)
      token_list[i]["text"].begin_offset -= value
      final_token_list[no].append(token_list[i])

  except Exception as e: 
    print(e)
    return []

  return final_token_list



if __name__ == '__main__':
  os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='your-credential.json'
  
  input_text_list = ["The story revolves around a girl.",
                "She is named after her red hooded.",
                "The girl walks through the woods.",
                "A Big Bad Wolf wants to eat the girl."]

  input_text_long = "The story revolves around a girl called Little Red Riding Hood. In Perrault's versions of the tale, she is named after her red hooded cape/cloak that she wears. The girl walks through the woods to deliver food to her sickly grandmother (wine and cake depending on the translation). In Grimms' version, her mother had ordered her to stay strictly on the path. A Big Bad Wolf wants to eat the girl and the food in the basket. He secretly stalks her behind trees, bushes, shrubs, and patches of little and tall grass. He approaches Little Red Riding Hood, who naively tells him where she is going. He suggests that the girl pick some flowers as a present for her grandmother, which she does. In the meantime, he goes to the grandmother's house and gains entry by pretending to be her. He swallows the grandmother whole (in some stories, he locks her in the closet) and waits for the girl, disguised as the grandma. When the girl arrives, she notices that her grandmother looks very strange. Little Red then says, \"What a deep voice you have!\" (\"The better to greet you with\", responds the wolf), \"Goodness, what big eyes you have!\" (\"The better to see you with\", responds the wolf), \"And what big hands you have!\" (\"The better to embrace you with\", responds the wolf), and lastly, \"What a big mouth you have\" (\"The better to eat you with!\", responds the wolf), at which point the wolf jumps out of the bed and eats her, too. Then he falls asleep. In Charles Perrault's version of the story (the first version to be published), the tale ends here. However, in later versions, the story continues generally as follows."

  # single input example
  response = analyze_syntax_single_input(input_text_long)
  print(str(response))

  # multiple input example
  responses = analyze_syntax_batch(input_text_list)
  for response in responses:
    print("==================================")
    print(str(response))





