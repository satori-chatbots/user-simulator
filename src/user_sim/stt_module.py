import speech_recognition as sr
import time
from openai import OpenAI
import warnings
from playsound import playsound
import pygame
from pydub import AudioSegment
import simpleaudio as sa


pygame.mixer.init()
warnings.filterwarnings("ignore", category=FutureWarning, module="whisper")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub")
client = OpenAI()
audio_format = "mp3"

# obtain audio from the microphone
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    r.energy_threshold = 50     # lower values for quieter rooms
    r.pause_threshold = 1
    audio = r.listen(source)


try:
    # for testing purposes, we're just using the default API key
    # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
    # instead of `r.recognize_google(audio)`
    print("Recognizing...")
    start = time.time()
    text = r.recognize_whisper(audio)
    print("Recognition: " + text)
    end = time.time()
    print(f"Recognition time:  {end - start}")

    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format=audio_format
    ) as response:
        response.stream_to_file("audio_test/output." + audio_format)

    end_response = time.time()
    print(f"Response time: {end_response - end}")
    print("Playing...")

    pygame.mixer.music.load("audio_test/output." + audio_format)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    end_process = time.time()

    print(f"Process time: {end_process - start} ")
except sr.UnknownValueError:
    print("Google Speech Recognition could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Google Speech Recognition service; {0}".format(e))



