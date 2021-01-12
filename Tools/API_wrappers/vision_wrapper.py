import io
import os
import sys
from google.cloud import vision
from google.cloud.vision import types
from PIL import Image
import base64



# helper function for debugging
def print_result(response, features):
  if not response:
    print('Error')
    return

  for feature in features:

    print('========='+str(feature)+'=========')

    if feature == vision.enums.Feature.Type.OBJECT_LOCALIZATION:
      objects = response.localized_object_annotations
      for object in objects:
        print(str(object.name)+'  '+str(object.score))

    if feature == vision.enums.Feature.Type.FACE_DETECTION:
      faces = response.face_annotations
      for face in faces:
        print(str(face.score))
   
    if feature == vision.enums.Feature.Type.LABEL_DETECTION:
      labels = response.label_annotations
      for label in labels:
        print(str(label.description)+'  '+str(label.score))
  

# if image too large, clip
# 640*480 is suggested size
SUGGEST_SIZE = [640,480]
def read_image(file_name, allow_resize=True):
  img = Image.open(file_name)
  buffer = io.BytesIO()
  img.save(buffer, 'JPEG')
  if allow_resize:
    width, depth = img.size
    proportion = max(width/SUGGEST_SIZE[0], depth/SUGGEST_SIZE[1])
    if proportion>=1 and width*depth>SUGGEST_SIZE[0]*SUGGEST_SIZE[1]:
      img.thumbnail((width/proportion, depth/proportion))
      # img.save('after_clip.jpeg') # for tesing only
  content = buffer.getvalue()
  return content

# wrapper function for one image
# support multiple features
def annotate_image(img_path, features, max_results=10, allow_resize=True):
  
  try:
    client = vision.ImageAnnotatorClient()

    file_name = os.path.join(os.path.dirname(__file__), img_path)
    content = read_image(file_name, allow_resize)

    features_json = []
    for feature in features:
      features_json.append({'type': feature,
                  'max_results': max_results})

    response = client.annotate_image({
      'image': {'content': content},
      'features': features_json,
    })

  except Exception as e: 
    print(e)
    return

  return response


# wrapper function for multiple image
# support multiple features
def annotate_batch_image(img_paths, features, max_results=10, allow_resize=True):
  
  try:
    client = vision.ImageAnnotatorClient()

    features_json = []
    for feature in features:
      features_json.append({'type': feature,
                  'max_results': max_results})

    requests = []
    for img_path in img_paths:
      file_name = os.path.join(os.path.dirname(__file__), img_path)
      content = read_image(file_name, allow_resize)
      requests.append({'image': {'content': content}, 'features': features_json})

    response = client.batch_annotate_images(requests)

  except Exception as e: 
    print(e)
    return

  return response




if __name__ == '__main__':
  os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='your-credential.json'
  img_file = 'data/label.jpeg'
  img_file2 = 'data/street.jpeg'

  # more features could be founded on Google Cloud Vsion Website (https://cloud.google.com/vision/docs/reference/rest/v1/Feature)
  # each feature refer to an API
  feature_list = [vision.enums.Feature.Type.OBJECT_LOCALIZATION,
                  vision.enums.Feature.Type.FACE_DETECTION,
                  vision.enums.Feature.Type.LABEL_DETECTION,
                  ]


  # one image, one API
  for feature in feature_list:
    response = annotate_image(img_file, [feature])
    print_result(response, [feature])

  # one image, multiple APIs
  response = annotate_image(img_file, feature_list)
  print_result(response, feature_list)


  # multiple images (small amount), one API
  # if there are more images, it would be better to use async API (https://cloud.google.com/vision/docs/batch)
  for feature in feature_list:
    responses = annotate_batch_image([img_file, img_file2], [feature])
    for response in responses.responses:
      print('========================= IMAGE =========================')
      print_result(response, [feature])


  # multiple images (small amount), multiple APIs
  responses = annotate_batch_image([img_file, img_file2], feature_list)
  for response in responses.responses:
    print('========================= IMAGE =========================')
    print_result(response, feature_list)
  



