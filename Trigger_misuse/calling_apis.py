import io, os, sys
from google.cloud import vision
from google.cloud.vision import types
from google.cloud import language_v1
from google.cloud.language_v1 import enums


def image_classification(img_path):
    vision_client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
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
        break


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


def detect_logos(img_path):
    vision_client = vision.ImageAnnotatorClient()
    file_name = os.path.join(
        os.path.dirname(__file__),
        img_path)
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.logo_detection(image=image)
    logos = response.logo_annotations

    for logo in logos:
        print(logo.description)

def sentiment_detection(text):
    client = language_v1.LanguageServiceClient()
    document    = language_v1.types.Document(
        content = text,
        type    = enums.Document.Type.PLAIN_TEXT)
    annotations = client.analyze_sentiment(document=document)
    score     = annotations.document_sentiment.score
    magnitude = annotations.document_sentiment.magnitude
    print(text+"\t\t"+str(score)+"\t"+str(magnitude))


if __name__ == '__main__':
  os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='your-credential.json'


