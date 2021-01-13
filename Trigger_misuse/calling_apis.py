import io, os, sys
from PIL import Image

from google.cloud import vision
from google.cloud.vision import types
from google.cloud import language_v1
from google.cloud.language_v1 import enums
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types
from google.cloud import texttospeech

# ========================================
# Google Cloud Vision
# Input: img_path: the file path of tested image, which must be smaller than 5MB
# ========================================

def read_image(img_path, target_width=640, target_depth=480):
    img = Image.open(file_name)
    if target_width>0 and target_depth>0:
        img = img.resize((target_width, target_depth))
    buffer = io.BytesIO()
    img.save(buffer, "JPEG")
    content = buffer.getvalue()
    return content


def image_classification(img_path):
    vision_client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)

    # if no resize
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    # if resize
    # content = read_image(file_name, target_width=640, target_depth=480)

    image = types.Image(content=content)
    response = vision_client.label_detection(image=image)
    labels = response.label_annotations
    for label in labels:
        print(str(label.description)+"  "+str(label.score))


def object_detection(img_path):
    client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)
    objects = client.object_localization(
        image=image).localized_object_annotations
    for object in objects:
        print(str(object.name)+"  "+str(object.score))


def text_detection(img_path):
    vision_client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations
    for text in texts:
        print('\n{}\t{}'.format(text.confidence,text.description))
        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices])
        print('bounds: {}'.format(','.join(vertices)))

def logo_detection(img_path):
    vision_client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)
    response = vision_client.logo_detection(image=image)
    logos = response.logo_annotations
    for logo in logos:
        print(logo.description)


def document_text_detection(img_path):
    vision_client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)
    response = vision_client.document_text_detection(image=image)
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            print('\nBlock confidence: {}\n'.format(block.confidence))
            for paragraph in block.paragraphs:
                print('Paragraph confidence: {}'.format(
                    paragraph.confidence))
                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    print('Word text: {} (confidence: {})'.format(
                        word_text, word.confidence))
                    for symbol in word.symbols:
                        print('\tSymbol: {} (confidence: {})'.format(
                            symbol.text, symbol.confidence))

def landmark_detection(img_path):
    vision_client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)
    response = vision_client.landmark_detection(image=image)
    landmarks = response.landmark_annotations
    for landmark in landmarks:
        print(landmark.description)


def face_detection(img_path):
    client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)
    response = client.face_detection(image=image)
    faces = response.face_annotations
    return faces
    # Names of likelihood from google.cloud.vision.enums
    chances = ('UNKNOWN', 'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE',
                       'LIKELY', 'VERY_LIKELY')
    for face in faces:
        print("Face:")
        print('anger: {}'.format(chances[face.anger_likelihood]))
        print('joy: {}'.format(chances[face.joy_likelihood]))
        print('surprise: {}'.format(chances[face.surprise_likelihood]))
        print('sorrow: {}'.format(chances[face.sorrow_likelihood]))
        print('headwear: {}'.format(chances[face.headwear_likelihood]))


def safe_search(img_path):
    client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)
    response = client.safe_search_detection(image=image)
    safe = response.safe_search_annotation
    print('adult: {}'.format(likelihood_name[safe.adult]))
    print('medical: {}'.format(likelihood_name[safe.medical]))
    print('spoofed: {}'.format(likelihood_name[safe.spoof]))
    print('violence: {}'.format(likelihood_name[safe.violence]))
    print('racy: {}'.format(likelihood_name[safe.racy]))


def web_search(img_path):
    client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)
    response = client.web_detection(image=image)
    annotations = response.web_detection
    if annotations.best_guess_labels:
        for label in annotations.best_guess_labels:
            print('\nBest guess label: {}'.format(label.label))

    if annotations.pages_with_matching_images:
        print('\n{} Pages with matching images found:'.format(
            len(annotations.pages_with_matching_images)))
        for page in annotations.pages_with_matching_images:
            print('\n\tPage url   : {}'.format(page.url))
            if page.full_matching_images:
                print('\t{} Full Matches found: '.format(
                       len(page.full_matching_images)))
                for image in page.full_matching_images:
                    print('\t\tImage url  : {}'.format(image.url))
            if page.partial_matching_images:
                print('\t{} Partial Matches found: '.format(
                       len(page.partial_matching_images)))
                for image in page.partial_matching_images:
                    print('\t\tImage url  : {}'.format(image.url))

    if annotations.web_entities:
        print('\n{} Web entities found: '.format(
            len(annotations.web_entities)))
        for entity in annotations.web_entities:
            print('\n\tScore      : {}'.format(entity.score))
            print(u'\tDescription: {}'.format(entity.description))

    if annotations.visually_similar_images:
        print('\n{} visually similar images found:\n'.format(
            len(annotations.visually_similar_images)))
        for image in annotations.visually_similar_images:
            print('\tImage url    : {}'.format(image.url))



# ========================================
# Google Cloud Language
# Input: text: a text string
# ======================================== 
def sentiment_detection(text):
    client = language_v1.LanguageServiceClient()
    document = language_v1.types.Document(content=text, type=enums.Document.Type.PLAIN_TEXT)
    response = client.analyze_sentiment(document=document)
    print(u"Document sentiment score: {}".format(response.document_sentiment.score))
    print(u"Document sentiment magnitude: {}".format(response.document_sentiment.magnitude))

def entity_detection(text):
    client = language_v1.LanguageServiceClient()
    document = language_v1.types.Document(content=text, type=enums.Document.Type.PLAIN_TEXT)
    response = client.analyze_entities(document=document)
    for entity in response.entities:
        print(u"Representative name for the entity: {}".format(entity.name))
        print(u"Entity type: {}".format(language_v1.Entity.Type(entity.type_).name))
        print(u"Salience score: {}".format(entity.salience))
        for metadata_name, metadata_value in entity.metadata.items():
            print(u"{}: {}".format(metadata_name, metadata_value))
        for mention in entity.mentions:
            print(u"Mention text: {}".format(mention.text.content))
            print(u"Mention type: {}".format(language_v1.EntityMention.Type(mention.type_).name))

def entity_sentiment_detection(text):
    client = language_v1.LanguageServiceClient()
    document = language_v1.types.Document(content=text, type=enums.Document.Type.PLAIN_TEXT)
    response = client.analyze_entity_sentiment(document=document)
    for entity in response.entities:
        print(u"Representative name for the entity: {}".format(entity.name))
        print(u"Entity type: {}".format(language_v1.Entity.Type(entity.type_).name))
        print(u"Salience score: {}".format(entity.salience))
        sentiment = entity.sentiment
        print(u"Entity sentiment score: {}".format(sentiment.score))
        print(u"Entity sentiment magnitude: {}".format(sentiment.magnitude))
        for metadata_name, metadata_value in entity.metadata.items():
            print(u"{} = {}".format(metadata_name, metadata_value))
        for mention in entity.mentions:
            print(u"Mention text: {}".format(mention.text.content))
            print(u"Mention type: {}".format(language_v1.EntityMention.Type(mention.type_).name))

def syntax_analysis(text):
    client = language_v1.LanguageServiceClient()
    document = language_v1.types.Document(content=text, type=enums.Document.Type.PLAIN_TEXT)
    response = client.analyze_syntax(document=document)
    for token in response.tokens:
        text = token.text
        print(u"Token text: {}".format(text.content))
        print(u"Location of this token in overall document: {}".format(text.begin_offset))
        part_of_speech = token.part_of_speech
        print(u"Part of Speech tag: {}".format(language_v1.PartOfSpeech.Tag(part_of_speech.tag).name))
        print(u"Voice: {}".format(language_v1.PartOfSpeech.Voice(part_of_speech.voice).name))
        print(u"Tense: {}".format(language_v1.PartOfSpeech.Tense(part_of_speech.tense).name))
        print(u"Lemma: {}".format(token.lemma))
        dependency_edge = token.dependency_edge
        print(u"Head token index: {}".format(dependency_edge.head_token_index))
        print(u"Label: {}".format(language_v1.DependencyEdge.Label(dependency_edge.label).name))

def text_classification(text):
    client = language_v1.LanguageServiceClient()
    document = language_v1.types.Document(content=text, type=enums.Document.Type.PLAIN_TEXT)
    response = client.classify_text(document=document)
    for category in response.categories:
        print(u"Category name: {}".format(category.name))
        print(u"Confidence: {}".format(category.confidence))



# ========================================
# Google Cloud Speech-to-text
# Input: audio_file: the file path of tested audio, mp3 format, sample_rate_hertz=48000
# ======================================== 
def transcribe_sync(audio_file):
    client = speech_v1p1beta1.SpeechClient()
    encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=48000,
        language_code='en-US')
    with io.open(audio_file, "rb") as f:
        content = f.read()
    audio = {"content": content}
    response = client.recognize(config, audio)
    for result in response.results:
        alternative = result.alternatives[0]
        print(u"Transcript: {}".format(alternative.transcript))

def transcribe_async(audio_file):
    client = speech_v1p1beta1.SpeechClient()
    encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=48000,
        language_code='en-US')
    with io.open(audio_file, "rb") as f:
        content = f.read()
    audio = {"content": content}
    operation = client.long_running_recognize(config, audio)
    print(u"Waiting for operation to complete...")
    response = operation.result()
    for result in response.results:
        alternative = result.alternatives[0]
        print(u"Transcript: {}".format(alternative.transcript))


# ========================================
# Google Cloud Text-to-Speech
# Input: text: a text string
# ======================================== 
def speech_synthesize(text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')

if __name__ == '__main__':
  os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='your-credential.json'
  # call API here


