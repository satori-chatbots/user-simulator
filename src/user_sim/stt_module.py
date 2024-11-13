import speech_recognition as sr
import time
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="whisper")
from metamorphic.rule_utils import language

# obtain audio from the microphone
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    r.energy_threshold = 50 # lower values for quieter rooms
    audio = r.listen(source)
    print("Recognizing...")

try:
    # for testing purposes, we're just using the default API key
    # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
    # instead of `r.recognize_google(audio)`
    start = time.time()
    print("Recognition: " + r.recognize_whisper(audio))
    # print("Recognition: " + r.recognize_google(audio))
    end = time.time()
    print(f"Recognition time:  {end - start}")
except sr.UnknownValueError:
    print("Google Speech Recognition could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Google Speech Recognition service; {0}".format(e))