import sys
import os
import io
import wave
from six.moves import queue
from time import sleep
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types

# Note to users:
# Config info availiable at:
# https://googleapis.dev/python/speech/latest/gapic/v1/types.html#google.cloud.speech_v1.types.RecognitionConfig
# https://googleapis.dev/python/speech/latest/gapic/v1/types.html#google.cloud.speech_v1.types.StreamingRecognitionConfig


# HELPER function: check the length, sample rate, and absolute length of audio
# audio_file: local audio file path
# return: a 3-tuple: (length, sample rate, absolute length) of audio
def _get_audio_length(audio_file):
  if ".mp3" in audio_file:
    from mutagen.mp3 import MP3
    # Below is one implementation, based on this: https://mutagen.readthedocs.io/en/latest/api/mp3.html
    audio = MP3(audio_file)
    length = int(audio.info.length)
    sample_rate = audio.info.sample_rate
  else:
    import soundfile as sf
    # Below is one implementation, based on this: https://github.com/bastibe/SoundFile
    f = sf.SoundFile(audio_file)
    abs_length = len(f)
    sample_rate = f.samplerate
    length = abs_length / sample_rate
  return (length, sample_rate)


# HELPER FUNCTION: determine the correct encoding, if certain misuses are detected
# filename: input file name in the WRAPPER FUNCTION
# encoding_used: user-specified encoding
# return: correct encoding 
def determine_encoding(filename, encoding_used):
  filetype = filename.split(".")[-1]
  if filetype == "mp3":
    if encoding_used != enums.RecognitionConfig.AudioEncoding.MP3:
      print("mp3 file specified, but encoding not using enums.RecognitionConfig.AudioEncoding.MP3")
      print("Changing encoding to Google STT API to be enums.RecognitionConfig.AudioEncoding.MP3")
      return enums.RecognitionConfig.AudioEncoding.MP3
  return encoding_used

# HELPER function: use recognize API
# audio_file: local audio file path
# return: result.alternatives[0]
def _STT_sync(audio_file, **kwargs):
  
  client = speech_v1p1beta1.SpeechClient()
  
  print("_STT_sync: Exeucting recognize API on audio_file {}".format(audio_file))

  config = kwargs

  with io.open(audio_file, "rb") as f:
      content = f.read()
  audio = {"content": content}

  transcript = ''
  response = client.recognize(config, audio)
  for result in response.results:
      # First alternative is the most probable result
      alternative = result.alternatives[0]
      transcript += alternative.transcript
  return transcript


def stream_feed(audio_file):
  
  f = io.open(audio_file, 'rb')
  
  f_size = os.stat(audio_file).st_size
  print(f_size)
  print(f_size / (1000*1024))
  
  it = 0

  while True:
    # Google mandates payload size to have limit 10485760 bytes
    # chunk = f.read(32 * 1024)
    chunk = f.read(1000 * 1024)
    it += 1
    
    if chunk == '' or it * (1000*1024) >= f_size:
      break
    sleep(0.1)
    print("Executing...")
    yield b''.join([chunk])
  print("Executed this")
  return


# HELPER function: use streaming_recognize API
# audio_file: local audio file path
# return: result.alternatives[0]
def _STT_stream(audio_file,  **kwargs):

  print("_STT_stream: Exeucting streaming_recognize API on audio_file {}".format(audio_file))

  client = speech_v1p1beta1.SpeechClient()
  # with io.open(audio_file, 'rb') as f:
      # content = f.read()

  config = kwargs
  streaming_config = types.StreamingRecognitionConfig(config=config)

  transcript = ''

  # In practice, stream should be a generator yielding chunks of audio data.
  stream = stream_feed(audio_file)
  requests = (types.StreamingRecognizeRequest(audio_content=chunk)
              for chunk in stream)

  # streaming_recognize returns a generator.
  # [START speech_python_migration_streaming_response]
  responses = client.streaming_recognize(streaming_config, requests)
  # [END speech_python_migration_streaming_request]

  for response in responses:
      # Once the transcription has settled, the first result will contain the
      # is_final result. The other results will be for subsequent portions of
      # the audio.
      for result in response.results:
          alternatives = result.alternatives
          for alternative in alternatives:
              transcript += alternative.transcript
  # [END speech_python_migration_streaming_response]
  # [END speech_transcribe_streaming]
  return transcript


# WRAPPER FUNCTION:
# The first argument must be path to local audio file
# The rest are keyword-arguments that are all optional. Refer to the URLs at the top of this file for more information
# Implementation: This wrapper uses *recognize* when the input size is smaller or equal to 60 seconds or *streaming_recognize* otherwise.  
def google_STT_wrapper(audio_file, 
                        encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16,
                        sample_rate_hertz = None,
                        audio_channel_count = 1,
                        enable_separate_recognition_per_channel = False,
                        language_code = 'en-US',
                        max_alternatives = 1,
                        profanity_filter = False,
                        speech_contexts = None,
                        enable_word_time_offsets = False,
                        enable_automatic_punctuation = False,
                        diarization_config = None,
                        metadata = None,
                        model = None,
                        use_enhanced = True):
  
  audio_length, sample_rate = _get_audio_length(audio_file)

  if sample_rate_hertz == None:
    sample_rate_hertz = sample_rate

  if enable_separate_recognition_per_channel and audio_channel_count <= 1:
    print("google_STT_wrapper: enable_separate_recognition_per_channel set to True but audio_channel_count <= 1, defaulting enable_separate_recognition_per_channel to False")
    enable_separate_recognition_per_channel = False

  encoding = determine_encoding(audio_file, encoding)

  kwargs = dict(encoding = encoding,
                        sample_rate_hertz = sample_rate_hertz,
                        audio_channel_count = audio_channel_count,
                        enable_separate_recognition_per_channel = enable_separate_recognition_per_channel,
                        language_code = language_code,
                        max_alternatives = max_alternatives,
                        profanity_filter = profanity_filter,
                        speech_contexts = speech_contexts,
                        enable_word_time_offsets = enable_word_time_offsets,
                        enable_automatic_punctuation = enable_automatic_punctuation,
                        diarization_config = diarization_config,
                        metadata = metadata,
                        model = model,
                        use_enhanced = use_enhanced)

  print("Audio length: {} sec".format(audio_length))


  if audio_length <= 60:
    result = _STT_sync(audio_file, **{k: v for k, v in kwargs.items() if v is not None})
  else:
    result = _STT_stream(audio_file, **{k: v for k, v in kwargs.items() if v is not None})

  return result

# Unit test cases below:
# if __name__ == "__main__":
  # result = google_STT_wrapper("data/15sec.mp3", encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16)
  # print(result)
  # result = google_STT_wrapper("data/lecture_140.wav", encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16)
  # print(result)