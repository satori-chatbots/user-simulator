import speech_recognition as sr
import time
from openai import OpenAI
import warnings
from playsound import playsound
import pygame
from pydub import AudioSegment
import simpleaudio as sa
import logging
logger = logging.getLogger('Info Logger')


pygame.mixer.init()
warnings.filterwarnings("ignore", category=FutureWarning, module="whisper")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub")
client = OpenAI()
audio_format = "mp3"

class STTModule:

    def __init__(self, energy_threshold=50, pause_threshold=1):

        self.energy_th = energy_threshold
        self.pause_th = pause_threshold

    def hear(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("Listening...")
            r.energy_threshold = self.energy_th  # lower values for quieter rooms
            r.pause_threshold = self.pause_th
            audio = r.listen(source)

        try:
            logger.info("Recognizing...")
            start = time.time()
            text = r.recognize_whisper(audio)
            end = time.time()
            logger.info(f"Recognition time:  {end - start}")
            return True, text
        except sr.UnknownValueError:
            logger.warning("Recognition model could not understand audio")
            return True, "Repeat, please."
        except sr.RequestError as e:
            logger.warning("Could not request results from Speech Recognition service; {0}".format(e))
            return False, None

    @staticmethod
    def say(message):

        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="alloy",
            input=message,
            response_format=audio_format
        ) as response:
            response.stream_to_file("audio_test/output." + audio_format)

        logger.info("Playing...")
        pygame.mixer.music.load("audio_test/output." + audio_format)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)